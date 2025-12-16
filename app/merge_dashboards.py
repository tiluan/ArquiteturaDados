import json
import os
import glob
import uuid
import copy
import re

# Configuration
DIRECTORY = "app/"
TRANSLATION_MAP_FILE = os.path.join(DIRECTORY, "translation_map.json")

def load_translation_map():
    if os.path.exists(TRANSLATION_MAP_FILE):
        with open(TRANSLATION_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

TRANSLATIONS = load_translation_map()

def translate(text):
    if not text:
        return text
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]
    return text

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')[:8]

def merge_dashboard_files(files, output_file):
    combined_data = {
        "datasets": [],
        "pages": [],
        "uiSettings": {},
        "widgets": []
    }

    final_datasets = []
    final_pages = []

    first_file_processed = False

    for fpath in files:
        filename = os.path.basename(fpath)
        print(f"Processing {filename}...")

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Skipping {filename}: {e}")
            continue

        if not first_file_processed and 'uiSettings' in data and data['uiSettings']:
            combined_data['uiSettings'] = data['uiSettings']
            first_file_processed = True

        dashboard_title = filename.replace('.lvdash.json', '')
        translated_dashboard_title = translate(dashboard_title)

        dashboard_id = generate_uuid()

        local_dataset_map = {}

        if 'datasets' in data:
            for ds in data['datasets']:
                original_id = ds['name']
                global_id = generate_uuid()

                new_ds = copy.deepcopy(ds)
                new_ds['name'] = global_id

                if 'displayName' in new_ds:
                    new_ds['displayName'] = translate(new_ds['displayName'])

                if 'parameters' in new_ds:
                    query_str = new_ds.get('query', '')
                    query_lines = new_ds.get('queryLines', [])

                    for param in new_ds['parameters']:
                        original_keyword = param['keyword']
                        new_keyword = f"{original_keyword}_{dashboard_id}"

                        param['keyword'] = new_keyword

                        original_display = param.get('displayName', original_keyword)
                        translated_display = translate(original_display)

                        param['displayName'] = f"{translated_dashboard_title}: {translated_display}"

                        pattern = r'(?<!\w):' + re.escape(original_keyword) + r'(?!\w)'

                        if query_str:
                            query_str = re.sub(pattern, f":{new_keyword}", query_str)

                        if query_lines:
                            new_lines = []
                            for line in query_lines:
                                new_lines.append(re.sub(pattern, f":{new_keyword}", line))
                            query_lines = new_lines

                    if query_str:
                        new_ds['query'] = query_str
                    if query_lines:
                        new_ds['queryLines'] = query_lines

                final_datasets.append(new_ds)
                local_dataset_map[original_id] = global_id

        if 'pages' in data:
            for page in data['pages']:
                new_page = copy.deepcopy(page)

                original_page_name = new_page.get('displayName', 'Untitled')
                translated_page_name = translate(original_page_name)

                new_page['displayName'] = f"{translated_dashboard_title}: {translated_page_name}"
                new_page['name'] = generate_uuid()

                if 'layout' in new_page:
                    for item in new_page['layout']:
                        if 'widget' in item:
                            widget = item['widget']
                            if 'queries' in widget:
                                for query in widget['queries']:
                                    if 'query' in query and 'datasetName' in query['query']:
                                        local_ds_id = query['query']['datasetName']
                                        if local_ds_id in local_dataset_map:
                                            query['query']['datasetName'] = local_dataset_map[local_ds_id]

                        if 'visualization' in widget:
                            vis = widget['visualization']
                            if 'title' in vis:
                                vis['title'] = translate(vis['title'])
                            if 'description' in vis:
                                vis['description'] = translate(vis['description'])

                        if 'description' in widget:
                             widget['description'] = translate(widget['description'])

                        if 'text' in widget:
                             widget['text'] = translate(widget['text'])

                final_pages.append(new_page)

    combined_data['datasets'] = final_datasets
    combined_data['pages'] = final_pages

    if 'theme' in combined_data['uiSettings']:
        combined_data['uiSettings']['theme']['visualizationColors'] = [
            "#0096FA", "#314D5A", "#F78DA7", "#FF6900", "#FCB900",
            "#7BDCB5", "#00D084", "#8ED1FC", "#0693E3", "#9B51E0"
        ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2)

    print(f"Success! Combined dashboard saved to {output_file}")
    print(f"Total Datasets: {len(final_datasets)}")
    print(f"Total Pages: {len(final_pages)}")

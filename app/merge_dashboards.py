import json
import os
import glob
import uuid
import copy
import re

# Configuration
DIRECTORY = "app/"
OUTPUT_FILE = os.path.join(DIRECTORY, "combined_dashboard.lvdash.json")
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
    # Direct match
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]
    return text

def generate_uuid():
    # Databricks seems to use 8-char hex strings
    return str(uuid.uuid4()).replace('-', '')[:8]

def merge_dashboards():
    files = glob.glob(os.path.join(DIRECTORY, "*.lvdash.json"))
    # Exclude the output file if it exists to avoid infinite recursion/duplication
    files = [f for f in files if os.path.abspath(f) != os.path.abspath(OUTPUT_FILE)]

    # Prioritize the dashboard with the best uiSettings
    preferred_ui_source = 'Account Usage Dashboard v2.lvdash.json'
    full_preferred_path = next((f for f in files if os.path.basename(f) == preferred_ui_source), None)

    if full_preferred_path:
        print(f"Prioritizing UI settings from {preferred_ui_source}")
        files.insert(0, files.pop(files.index(full_preferred_path)))

    combined_data = {
        "datasets": [],
        "pages": [],
        "uiSettings": {},
        "widgets": []
    }

    # Global merged lists
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

        # Copy uiSettings from the first file found (assuming consistency or at least a valid baseline)
        if not first_file_processed and 'uiSettings' in data and data['uiSettings']:
            combined_data['uiSettings'] = data['uiSettings']
            first_file_processed = True

        # Dashboard context
        dashboard_title = filename.replace('.lvdash.json', '')
        translated_dashboard_title = translate(dashboard_title)

        # ID for namespacing parameters per dashboard (file)
        # Using first 8 chars of a new uuid
        dashboard_id = generate_uuid()

        # Map local dataset ID -> Global dataset ID for this file
        local_dataset_map = {}

        # 1. Process Datasets
        if 'datasets' in data:
            for ds in data['datasets']:
                original_id = ds['name']

                # ALWAYS generate a new ID
                global_id = generate_uuid()

                new_ds = copy.deepcopy(ds)
                new_ds['name'] = global_id

                # Translate dataset displayName
                if 'displayName' in new_ds and ' ' in new_ds['displayName']:
                        new_ds['displayName'] = translate(new_ds['displayName'])

                # Handle Parameters Namespacing
                # We need to update parameter definitions AND the query using them
                if 'parameters' in new_ds:
                    query_str = new_ds.get('query', '')
                    query_lines = new_ds.get('queryLines', [])

                    for param in new_ds['parameters']:
                        original_keyword = param['keyword']
                        new_keyword = f"{original_keyword}_{dashboard_id}"

                        # Update definition
                        param['keyword'] = new_keyword

                        # Update display name to be clear in UI
                        # E.g. "Account Usage: Workspace"
                        original_display = param.get('displayName', original_keyword)
                        translated_display = translate(original_display)

                        param['displayName'] = f"{translated_dashboard_title}: {translated_display}"

                        # Regex to replace :keyword in query
                        # Look for :keyword followed by non-word char or end of string
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

        # 2. Process Pages
        if 'pages' in data:
            for page in data['pages']:
                new_page = copy.deepcopy(page)

                # Update Page Name/Title
                original_page_name = new_page.get('displayName', 'Untitled')
                translated_page_name = translate(original_page_name)

                # Prefix with Dashboard Name to distinguish
                new_page['displayName'] = f"{translated_dashboard_title}: {translated_page_name}"

                # Generate new page ID to avoid collisions
                new_page['name'] = generate_uuid()

                # Process Widgets inside Javascript structure if nested?
                if 'widgets' in new_page:
                    for widget in new_page['widgets']:
                        # Remap dataset reference
                        if 'dataset' in widget and 'name' in widget['dataset']:
                            local_ds_id = widget['dataset']['name']
                            if local_ds_id in local_dataset_map:
                                widget['dataset']['name'] = local_dataset_map[local_ds_id]
                            else:
                                pass # Should not happen

                        # Translate Widget Titles/Descriptions
                        if 'visualization' in widget:
                            vis = widget['visualization']
                            if 'title' in vis:
                                vis['title'] = translate(vis['title'])
                            if 'description' in vis:
                                vis['description'] = translate(vis['description'])

                        if 'description' in widget:
                             widget['description'] = translate(widget['description'])

                        # Check for text widgets (markdown)
                        if 'text' in widget:
                             widget['text'] = translate(widget['text']) # Naive text replacement

                final_pages.append(new_page)

    combined_data['datasets'] = final_datasets
    combined_data['pages'] = final_pages

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2)

    print(f"Success! Combined dashboard saved to {OUTPUT_FILE}")
    print(f"Total Datasets: {len(final_datasets)}")
    print(f"Total Pages: {len(final_pages)}")

if __name__ == "__main__":
    merge_dashboards()

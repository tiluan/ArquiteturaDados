import json
import os
import glob

directory = "c:/MyProjects/Databricks Observability"
files = glob.glob(os.path.join(directory, "*.lvdash.json"))

all_datasets = {}
all_pages = []

for fpath in files:
    print(f"--- Analyzing {os.path.basename(fpath)} ---")
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Top-level keys: {list(data.keys())}")

        if 'datasets' in data:
            print(f"Number of datasets: {len(data['datasets'])}")
            for ds in data['datasets']:
                if ds['name'] in all_datasets:
                    print(f"  WARNING: Dataset ID collision: {ds['name']}")
                all_datasets[ds['name']] = ds

        if 'pages' in data:
            print(f"Number of pages: {len(data['pages'])}")
            for page in data['pages']:
                print(f"  Page Name: {page.get('name', 'Unknown')}, DisplayName: {page.get('displayName', 'Unknown')}")

        if 'widgets' in data:
             print(f"Number of widgets (root): {len(data['widgets'])}")

    except Exception as e:
        print(f"Error reading {fpath}: {e}")
    print("\n")

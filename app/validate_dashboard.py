import json
import os

DASHBOARD_FILE = "app/1-Custos_e_FinOps.lvdash.json"
REFERENCE_FILE = "app/Account Usage Dashboard v2.lvdash.json"

def validate():
    print("Loading combined dashboard...")
    with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Loading reference dashboard...")
    with open(REFERENCE_FILE, 'r', encoding='utf-8') as f:
        ref_data = json.load(f)

    # 1. Check ID formats
    print("\n--- Checking ID Formats ---")
    dataset_ids = [ds['name'] for ds in data.get('datasets', [])]
    page_ids = [p['name'] for p in data.get('pages', [])]

    print(f"Sample Dataset ID: {dataset_ids[0] if dataset_ids else 'None'} (Len: {len(dataset_ids[0]) if dataset_ids else 0})")
    print(f"Sample Page ID: {page_ids[0] if page_ids else 'None'} (Len: {len(page_ids[0]) if page_ids else 0})")

    ref_ds_ids = [ds['name'] for ds in ref_data.get('datasets', [])]
    print(f"Ref Dataset ID: {ref_ds_ids[0] if ref_ds_ids else 'None'} (Len: {len(ref_ds_ids[0]) if ref_ds_ids else 0})")

    # 2. Check Dataset References in Widgets
    print("\n--- Checking Widget Dataset References ---")
    missing_refs = 0
    total_refs = 0

    dataset_id_set = set(dataset_ids)

    for page in data.get('pages', []):
        for widget in page.get('widgets', []):
            if 'dataset' in widget and 'name' in widget['dataset']:
                ds_ref = widget['dataset']['name']
                total_refs += 1
                if ds_ref not in dataset_id_set:
                    print(f"ERROR: Widget in page '{page.get('displayName')}' references missing dataset: {ds_ref}")
                    missing_refs += 1

    if missing_refs == 0:
        print("All widget dataset references are valid.")
    else:
        print(f"Found {missing_refs} missing dataset references out of {total_refs}.")

    # 3. Check uiSettings
    print("\n--- Checking uiSettings ---")
    print(f"Combined uiSettings: {json.dumps(data.get('uiSettings'), indent=2)}")
    print(f"Reference uiSettings: {json.dumps(ref_data.get('uiSettings'), indent=2)}")

if __name__ == "__main__":
    validate()

import os
from merge_dashboards import merge_dashboard_files

DIRECTORY = "app/"

THEMED_DASHBOARDS = {
    "1-Custos_e_FinOps": [
        "Account Usage Dashboard v2.lvdash.json",
        "DBSQL Cost Dashboard (PrPr).lvdash.json",
        "Model Serving Cost Attribution.lvdash.json",
        "azure-serverless-jobs-and-notebooks-cost-observability.lvdash.json"
    ],
    "2-Observabilidade_de_Pipelines_e_Jobs": [
        "Jobs System Tables Dashboard.lvdash.json",
        "LakeFlow System Tables Dashboard v0.1.lvdash.json"
    ],
    "3-Governanca_de_Metadados": [
        "databricks-assistant-metrics.lvdash.json"
    ]
}

def build_dashboards():
    for theme, files in THEMED_DASHBOARDS.items():
        print(f"Building {theme} dashboard...")

        if not files:
            print(f"No files found for theme {theme}. Skipping.")
            continue

        input_files = [os.path.join(DIRECTORY, f) for f in files]
        output_file = os.path.join(DIRECTORY, f"{theme}.lvdash.json")

        merge_dashboard_files(input_files, output_file)

if __name__ == "__main__":
    build_dashboards()

from ruamel.yaml import YAML
from openpyxl import load_workbook

yaml = YAML()
yaml.preserve_quotes = True

workbook = load_workbook("3d-print/Roll-Catalog.xlsx", read_only=True, data_only=True)
rows = workbook.active.iter_rows(values_only=True)
headers = next(rows)
name_column = headers.index("Name")
filament_names = sorted(
    [row[name_column] for row in rows if row[name_column]],
    key=str.casefold,
)
workbook.close()

with open(".github/ISSUE_TEMPLATE/print-request.yml") as f:
    template = yaml.load(f)

for field in template["body"]:
    if field.get("id") == "filaments":
        field["attributes"]["options"] = filament_names
        break

with open(".github/ISSUE_TEMPLATE/print-request.yml", "w") as f:
    yaml.dump(template, f)

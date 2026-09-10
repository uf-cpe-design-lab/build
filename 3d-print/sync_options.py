from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

with open("3d-print/filament-list.yml") as f:
    source = yaml.load(f)

with open(".github/ISSUE_TEMPLATE/print-request.yml") as f:
    template = yaml.load(f)

for field in template["body"]:
    if field.get("id") == "filaments":  # match by id
        field["attributes"]["options"] = source["filament"]
        break

with open(".github/ISSUE_TEMPLATE/print-request.yml", "w") as f:
    yaml.dump(template, f)

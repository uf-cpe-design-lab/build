import json
import subprocess
import re
import glob
import os
import requests

with open("request.json", "r") as file:
    request = json.load(file)

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_OWNER = os.environ["REPO_OWNER"]
REPO_NAME = os.environ["REPO_NAME"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])
ISSUE_NODE_ID = os.environ["ISSUE_NODE_ID"]

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def close_issue():
    requests.patch(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}",
        headers=headers,
        json={"state": "closed", "state_reason": "not_planned"}
    )

def graphql(query, variables={}):
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        json={"query": query, "variables": variables}
    )
    return response.json()

def add_to_project_queued(print_time, needed_by):
    result = graphql("""
        query($owner: String!, $number: Int!) {
            organization(login: $owner) {
                projectV2(number: $number) {
                    id
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options { id name }
                            }
                            ... on ProjectV2Field {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
    """, {"owner": REPO_OWNER, "number": PROJECT_NUMBER})

    project = result["data"]["organization"]["projectV2"]
    project_id = project["id"]
    fields = project["fields"]["nodes"]

    status_field = next(f for f in fields if f.get("name") == "Status")
    queued_option_id = next(o["id"] for o in status_field["options"] if o["name"] == "Queued")
    print_time_field = next(f for f in fields if f.get("name") == "Print Time")
    needed_by_field = next(f for f in fields if f.get("name") == "Needed By")

    add_result = graphql("""
        mutation($projectId: ID!, $contentId: ID!) {
            addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
                item { id }
            }
        }
    """, {"projectId": project_id, "contentId": ISSUE_NODE_ID})
    
    print("Add result: ", json.dumps(add_result, indent=2))
    item_id = add_result["data"]["addProjectV2ItemById"]["item"]["id"]

    def update_field(field_id, value):
        graphql("""
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: $value
                }) {
                    projectV2Item { id }
                }
            }
        """, {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "value": value})

    update_field(status_field["id"], {"singleSelectOptionId": queued_option_id})
    update_field(print_time_field["id"], {"text": print_time})
    update_field(needed_by_field["id"], {"date": needed_by})

text = request["model_url"]
url = re.search(r'\((https?://[^\)]+)\)', text).group(1)

subprocess.run(["curl", "-L", "-o", "file.zip", "-A", "Mozilla/5.0", url])  # Download file
subprocess.run(["unzip", "file.zip"])  # Unzip file

# Supports
match request["supports"].lower():
    case "auto (slicer decides)":
        support = "--support-material --support-material-auto"
    case "no supports":
        support = ""
    case "everywhere":
        support = "--support-material"
    case "build plate only":
        support = "--support-material --support-material-buildplate-only"

# Height parse
height = request["layer_height"].split(" ")[0]

stl_files = glob.glob("*.stl")

cmd = [
    "prusa-slicer",
    "--export-gcode",
    "--layer-height", height,
    "--fill-density", request["infill"],
    "--output", "output.gcode",
] + stl_files

if support:
    cmd.extend(support.split())
try:
    subprocess.run(cmd, check=True)
    # Time parsing
    with open("output.gcode", "r") as f:
        content = f.read()

        time = ""
        match = re.search(r"estimated printing time \(normal mode\) = (.+)", content)
        if match:
            time = match.group(1)
        with open("comment", "x", encoding="utf-8") as f:
            f.write(f"""
    Print request successful!
    ----------------------------------------------
    Your estimated print time is: {time}
    """)
        add_to_project_queued(time, request["deadline"] if request["deadline"] else None)
except:
    with open("comment", "x", encoding="utf-8") as f:
        f.write("""
Print Request Failed!
----------------------------------------------
There was either an issue with your .stl file or you submitted the wrong file!
Please resubmit and ensure the following:
1. Your file has the .stl extension
2. You are submitting ONE file to be printed
3. Your file is in a zip archive
""")
        close_issue()

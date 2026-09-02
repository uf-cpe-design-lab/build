import json
import subprocess
import re
import glob

with open("request.json", "r") as file:
    request = json.load(file)

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
    subprocess.run(cmd, capture_output=True, text=True)
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
else:
    # Time parsing
    with open("output.gcode", "r") as f:
        content = f.read()

    time = ""
    match = re.search(r"estimated printing time \(normal mode\) = (.+)", content)
    if match:
        time = match.group(1)
WebWork Accessibility
    with open("comment", "x", encoding="utf-8") as f:
        f.write(f"""
Print request successful!
----------------------------------------------
Your estimated print time is: {time}
""")

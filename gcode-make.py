import json
import subprocess
import re

with open("request.json", "r") as file:
    request = json.load(file)

text = request["model_url"]
url = re.search(r'\((https?://[^\)]+)\)', text).group(1)

subprocess.run(f"curl -L -o file.zip {url}") # Download file

subprocess.run("unzip file.zip") # Unzip file

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

subprocess.run([
"prusa-slicer",
"--export-gcode",
"--layer-height", request["height"],
"--fill-density", request["infill"],
"--material-profile", request["material"],
    support
    "--output output.gcode"
])

# Time parsing
with open("output.gcode", "r") as f:
    content = f.read()

time = ""
match = re.search(r"estimated printing time \(normal mode\) = (.+)", content)
if match:
    time = match.group(1)  # '1h 23m 45s'

with open("comment", "x", encoding="utf-8") as f:
    f.write(f"""
Print request successful!
----------------------------------------------
Your estimated print time is: {time}
""")

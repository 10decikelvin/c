EDFs refer to Edexia Dataset Files, which contain student submissions with grades. EGFs refer to Edexia Grading files, which contain the grading result of any automated essay scoring (AES) algorithm

For pointers/docs about how to interact with the edf/egf file formats using a python SDK / file format best practices, refer to:
- https://raw.githubusercontent.com/Edexia/edf/refs/heads/main/README.md
- https://raw.githubusercontent.com/Edexia/egf/refs/heads/main/README.md

You MUST use uv in this project: this is both for package management  (`uv add xxx`) and for code execution (`uv run xxx` or `uv grade xxx`). This project is a cli tool (a uv tool called c) that takes as command line arguments a list of egf files and outputs a self contained .html containing all necessary information that can be opened. If you ever need test egf/edf files, there are some example ones in d/. Don't move them out of the folder, as they are sensitive.
import json
import sys

## Select files and directories over a certain file size.
## Avoids overcounting children of selected directories.

with open("find.json") as f:
    indict = json.load(f)

outdict = {
        "completed": [],
        "queued": [],
        "failed": [],
        }

### SCRIPT ARGUMENTS

## Root directory; Quit if not provided
try:
    root = sys.argv[1]
except Exception:
    print("Please enter a directory")
    quit(0)

## Log base 2 of the min size threshold in bytes; Default 12 (one terabyte)
try:
    exp = int(sys.argv[2])
except Exception:
    exp = 12

### ENTRY SELECTION

def read(base, structure):

    struct_name = structure[0]
    struct_type = structure[1]
    struct_children = structure[2:-1]
    struct_size = structure[-1]

    print_parent = True
    if struct_size > 10**exp:
        print_parent = False

        for child in struct_children:
            child_name = child[0]
            child_path = base + "/" + child_name
            if read(child_path, child):
                outdict["queued"].append(child_path)

    return print_parent

### WRITE

read(root, indict)
with open("select.json", "w") as f:
    json.dump(outdict, f)
    f.write("\n")

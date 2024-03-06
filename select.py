import json
import sys

with open("find.json") as f:
    indict = json.load(f)

outdict = {
        "completed": [],
        "queued": [],
        "failed": [],
        }

try:
    root = sys.argv[1]
except Exception:
    print("Please enter a directory")
    quit(0)

try:
    exp = int(sys.argv[2])
except Exception:
    exp = 12

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

read(root, indict)
with open("select.json", "w") as f:
    json.dump(outdict, f)

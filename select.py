import json
import sys
import argparse

parser = argparse.ArgumentParser(
    prog='select.py',
    description=
    """
Select files and directories over a certain file size.
Avoids overcounting children of selected directories.
    """
)
parser.add_argument('root', help='path to the root directory')
parser.add_argument('--file-tree', help='path to the file tree')
parser.add_argument('--selection', help='path to the top directory to upload')
parser.add_argument('--min-size', type=int, help='largest size (in bytes) to upload separately')
parser.add_argument('-o', '--out', help='outfile')
args = parser.parse_args()

with open(args.file_tree) as f:
    indict = json.load(f)

outdict = {
    "completed": [],
    "queued": [],
    "failed": [],
}

### ENTRY SELECTION

def common_origin(a, b):
    a += "/"
    b += "/"
    return a.startswith(b) or b.startswith(a)

def read(base, structure):

    struct_name = structure[0]
    struct_type = structure[1]
    struct_children = structure[2:-1]
    struct_size = structure[-1]

    print_parent = common_origin(args.selection, base)
    if struct_size > args.min_size:
        print_parent = False

        for child in struct_children:
            child_name = child[0]
            child_path = base + "/" + child_name
            if read(child_path, child):
                outdict["queued"].append(child_path)

    return print_parent

### WRITE

read(args.root, indict)
with open(args.out, "w") as f:
    json.dump(outdict, f)
    f.write("\n")

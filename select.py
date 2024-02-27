import json
import sys

file = open("find.json")
d = json.load(file)

root = sys.argv[1]

def read(base, structure):

    struct_name = structure[0]
    struct_type = structure[1]
    struct_children = structure[2:-1]
    struct_size = structure[-1]

    print_parent = True
    if struct_size > 1e12:
        print_parent = False

        for child in struct_children:
            child_name = child[0]
            child_path = base + "/" + child_name
            if read(child_path, child):
                print(child_path)

    return print_parent

read(root, d)

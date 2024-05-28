import os
from enum import IntEnum
from functools import total_ordering
from multiprocessing import Pool
import sys
import argparse
import json

# ========
# Filesystem JSON tree generator
#
# Generates a JSON tree of the files and directories, 
# including their sizes (in bytes), recursively calculated for directories
# ========

# Entry_type: Differentiates directories and various file types.
# Currently only has one generic file type.
class Entry_type(IntEnum):
    UNKNOWN = -1
    DIRECTORY = 0
    FILE = 1

# An Entry describes a directory or file with the following attributes:
# - path: string. The entry's absolute path.
# - name: string. The entry base name.
# - type: int. The enum of the entry type given by Entry_type.
# - size: int. The byte size of the entry, calculated recursively for directories.
# - children: Array<Entry>. The entry's files and subdirectories, if they exist.
# It is ordered such that directories are before files (compare_type), 
# then alphabetically (compare_name).
@total_ordering
class Entry:
    def __init__(self, path, depth=0):
        self.path = path
        self.depth = depth
        self.name = os.path.basename(path) 
        self.type = Entry_type.UNKNOWN
        self.size = 0
        self.children = list()

        if os.path.isdir(path):
            self.type = Entry_type.DIRECTORY
        elif os.path.isfile(path):
            self.type = Entry_type.FILE

    # tree node representation
    def node(self):
        return [ self.name, int(self.type), self.size, *[ child.node() for child in sorted(self.children) ] ]

    # string representation
    def __str__(self):
        return json.dumps(self.node(), separators=(',', ':'))

    # equality comparator
    def __eq__(self, other):
        return ((self.type, self.name) == (other.type, other.name))

    # less than comparator
    def __lt__(self, other):
        return ((self.type, self.name) < (other.type, other.name))

# Recursively traverses filesystem tree, printing entry names, types, and sizes.
# The sizes of directories are calculated recursively.
def traverse(entry, parallel=False):
    if entry.type == Entry_type.DIRECTORY:
        if entry.depth == args.depth: return entry

        child_depth = entry.depth + 1
        entry.children = sorted([ Entry( os.path.join(entry.path, child_name), depth=child_depth ) for child_name in os.listdir(entry.path) ])

        if parallel:
            entry.children = list(map(traverse_parallel, entry.children))
        elif (len(entry.children) >= args.minproc) and (args.nproc > 1):
            with Pool(args.nproc) as pool:
                entry.children = list(pool.map(traverse_parallel, entry.children))
        else:
            entry.children = list(map(traverse, entry.children))

        entry.size = sum(child.size for child in entry.children)

    elif entry.type == Entry_type.FILE:
        try:
            entry.size = os.path.getsize(entry.path)
        except OSError as e:
            sys.stderr.write(e.strerror)
            sys.stderr.flush()

    return entry

def traverse_parallel(entry):
    return traverse(entry, parallel=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='find.py',
        description=
"""Filesystem JSON tree generator
  Generates a JSON tree of the files and directories,
  including their sizes (in bytes), recursively calculated for directories.

Each entry in tree has the structure
[ <name>, <type>, <size>, <child 1>, <child 2>, ... ]
  <name>      name of file or directory
  <type>      0 for directory, 1 for file
  <size>      size of file or directory (including children), in bytes
  <child N>   child entries (if any), in the same Entry schema
    """
    )
    parser.add_argument('root', help='path to the root directory')
    parser.add_argument('--depth', type=int, default=-1, help="maximum search depth; -1=infinity")
    parser.add_argument('--nproc', type=int, default=1, help="maximum number of multiprocessing processes to use")
    parser.add_argument('--minproc', type=int, default=1, help="minimum number of multiprocessing processes to use")
    parser.add_argument('-o', '--out', help='output file')
    args = parser.parse_args()

    root_entry = Entry(args.root, depth=0)
    traverse(root_entry)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(root_entry.node(), f, separators=(',', ':'))
            f.write("\n")
    else:
        print(root_entry)


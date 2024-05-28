import os
from enum import IntEnum
from functools import total_ordering
import sys
import argparse

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

# An Entry is a directory or a file with the following attributes:
# - path: string. The entry's absolute path.
# - name: string. The entry name. Cannot contain the " character
# - type: int. The enum of the entry type given by Entry_type.
# It is ordered such that directories are before files (compare_type), 
# then alphabetically (compare_name).
@total_ordering
class Entry:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path) 
        self.type = Entry_type.UNKNOWN

        if os.path.isdir(path):
            self.type = Entry_type.DIRECTORY
        elif os.path.isfile(path):
            self.type = Entry_type.FILE

    # equality comparator
    def __eq__(self, other):
        return ((self.type, self.name) == (other.type, other.name))

    # less than comparator
    def __lt__(self, other):
        return ((self.type, self.name) < (other.type, other.name))

# Recursively traverses filesystem tree, printing entry names, types, and sizes.
# The sizes of directories are calculated recursively.
def traverse(entry, depth):
    size = 0

    sys.stdout.write(f'["{ entry.name }", { entry.type }')

    if entry.type == Entry_type.DIRECTORY:
        if depth != 0:
            children = sorted([ Entry(child_path) for child_path in os.scandir(entry.path) ])
            for child_entry in children:
                sys.stdout.write(',')
                size += traverse(child_entry, depth - 1)

    elif entry.type == Entry_type.FILE:
        try:
            size = os.path.getsize(entry.path)
        except OSError as e:
            sys.stderr.write(e.strerror)
            sys.stderr.flush()
            size = 0

    sys.stdout.write(f',{ size }]')
    return size

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='find.py',
        description=
"""Filesystem JSON tree generator
  Generates a JSON tree of the files and directories,
  including their sizes (in bytes), recursively calculated for directories.

Each node in tree has the structure
[ <name>, <child 1>, <child 2>, ... , <type>, <size> ]
  <name>   \tname of file or directory
  <child N>\tchild node for child file or directory
  <type>   \t0 for directory, 1 for file
  <size>   \tsize of file or directory (including children), in bytes
    """
    )
    parser.add_argument('root', help='path to the root directory')
    parser.add_argument('--depth', type=int, default=-1, help='maximum crawl depth; -1=infinity')
    args = parser.parse_args()

    traverse(Entry(args.root), int(args.depth))
    sys.stdout.write('\n')




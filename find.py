import os
from enum import IntEnum
from functools import total_ordering
from concurrent.futures import ThreadPoolExecutor
import sys
import argparse
import json

# ========
# Filesystem JSON tree generator
#
# Generates a JSON tree of the files and directories, 
# including their sizes (in bytes), recursively calculated for directories
# ========

class col:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
                
    UNDOLINE = '\033[A\33[2KT\r'

class Log:
    def __init__(self):
        self.state = dict()
        self.n = 0
    def queue(self, path):
        self.state[path] = col.OKBLUE + 'Queued \t' + col.ENDC
        self.log()
        self.n += 1
    def finish(self, path):
        self.state[path] = col.OKGREEN + 'Crawled\t' + col.ENDC
        self.log()
    def log(self):
        print(
                col.UNDOLINE * self.n 
                + "\n".join(status + path for (path, status) in sorted(self.state.items()))
        )

# Entry_type: Differentiates directories and various file types.
# Currently only has one generic file type.
class Entry_type(IntEnum):
    UNKNOWN = -1
    DIRECTORY = 0
    FILE = 1

# An Entry describes a directory or file with the following attributes:
# - path: string. This entry's absolute path.
# - depth: int. This entry's distance to the root entry.
# - name: string. This entry's base name.
# - type: int. The enum of this entry's type, given by Entry_type.
# - size: int. This entry's byte size, calculated recursively for directories.
# - children: Array<Entry>. This entry's files and subdirectories, if they exist.
# It is ordered such that directories are before files (compare_type), then alphabetically (compare_name).
# Only the name, type, size, and children are included in the final JSON tree
@total_ordering
class Entry:
    def __init__(self, path, depth=0):
        self.path = path
        self.depth = depth
        self.name = os.path.basename(path) 
        self.type = Entry_type.UNKNOWN
        self.size = 0
        if self.depth <= args.log_depth:
            log.queue(self.path)
        self.executor = executor.submit(self.os)

    # I/O intensive operations, to be done in thread pool
    def os(self):
        if os.path.isdir(self.path):
            self.type = Entry_type.DIRECTORY
            if self.depth == args.depth:
                self.children = list()
            else:
                self.children = [ Entry( os.path.join(self.path, child_name), depth=self.depth+1) for child_name in os.listdir(self.path) ]
        elif os.path.isfile(self.path):
            self.type = Entry_type.FILE
            self.size = os.path.getsize(self.path)

    # tree node representation
    def node(self):
        self.executor.result()
        child_nodes = list()
        if self.type == Entry_type.DIRECTORY:
            child_nodes = [ child.node() for child in sorted(self.children) ]
            self.size = sum( child.size for child in self.children )
        if self.depth <= args.log_depth:
            log.finish(self.path)
        return [ self.name, int(self.type), self.size, *child_nodes ]

    # string representation
    def __str__(self):
        return json.dumps(self.node(), separators=(',', ':'))

    # equality comparator
    def __eq__(self, other):
        return ((self.type, self.name) == (other.type, other.name))

    # less than comparator
    def __lt__(self, other):
        return ((self.type, self.name) < (other.type, other.name))

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
    parser.add_argument('--log-depth', type=int, default=2, help="maximum log depth")
    parser.add_argument('--nproc', type=int, default=1, help="maximum number of multiprocessing processes to use")
    parser.add_argument('-o', '--out', help='output file')
    args = parser.parse_args()

    executor = ThreadPoolExecutor(max_workers=args.nproc)
    log = Log()
    root_entry = Entry(args.root, depth=0)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(root_entry.node(), f, separators=(',', ':'))
            f.write("\n")
    else:
        print(root_entry)


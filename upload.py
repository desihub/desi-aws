import sys
import os
from os import system, path

max_dirs = 8

root = sys.argv[1]

bucket = "s3://desiproto"

file = open("select.txt")
subdirs = file.read().splitlines()
subdirs_len = len(subdirs)

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

for (index, subdir) in enumerate(subdirs):
    if index == max_dirs: 
        print(f"{col.OKBLUE} Exceeded maximum directory debug limit. Stopping... {col.ENDC}")
        break

    header = f"[ {index+1}/{subdirs_len} ]"

    abspath = path.abspath(subdir)
    isdir = path.isdir(abspath)
    relpath = path.relpath(abspath, root)

    cmd = "cp"

    if isdir:
        abspath += "/"
        relpath += "/"
        cmd = "sync"

    print(f"{col.BOLD} {col.OKGREEN} {header} {col.OKCYAN} Syncing \"{relpath}\" with s5cmd... {col.ENDC}")

    s5cmd = os.system(f"s5cmd --numworkers 16 {cmd} {abspath} {bucket}/{relpath}")
    if os.waitstatus_to_exitcode(s5cmd) == 0:
        continue

    print(f"{col.BOLD} {col.WARNING} {header} {col.OKCYAN} Failed to sync \"{relpath}\" with s5cmd. Retrying with aws-cli... {col.ENDC}")
    awscli = os.system(f"aws s3 {cmd} {abspath} {bucket}/{relpath}")
    if os.waitstatus_to_exitcode(awscli) == 0:
        continue

    print(f"{col.BOLD} {col.FAIL} {header} Failed to sync \"{relpath}\" with awscli! {col.ENDC}")
    sys.stderr.write(abspath + "\n")

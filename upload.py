import sys
import os
import json
from os import system, path

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

### INPUTS

try:
    root = sys.argv[1]
except Exception:
    print("Please enter a directory")
    quit(0)

try:
    max_dirs = int(sys.argv[2])
except Exception:
    max_dirs = 8
print(f"{col.OKGREEN} Uploading a maximum of {max_dirs} directories... {col.ENDC}")

with open("select.json") as f:
    select = json.load(f)

subdirs = select["queued"]
subdirs_len = len(subdirs)

### OUTPUTS

def write(data):
    with open("select.json", "w") as f:
        json.dump(data, f)

bucket = "s3://desiproto"

### UPLOADS

for (index, subdir) in enumerate(subdirs):
    if index == max_dirs: 
        print(f"{col.OKBLUE} Finished uploading {max_dirs} directories. Stopping... {col.ENDC}")
        break

    header = f"[ {index+1}/{subdirs_len} ]"

    abspath = path.abspath(subdir)
    isdir = path.isdir(abspath)
    relpath = path.relpath(abspath, root)

    select["queued"].remove(subdir) 

    cmd = "cp"

    if isdir:
        abspath += "/"
        relpath += "/"
        cmd = "sync"

    print(f"{col.BOLD} {col.OKGREEN} {header} {col.OKCYAN} Syncing \"{relpath}\" with s5cmd... {col.ENDC}")

    s5cmd = os.system(f"s5cmd --numworkers 16 --log error --stat {cmd} {abspath} {bucket}/{relpath}")
    if os.waitstatus_to_exitcode(s5cmd) == 0: # if successful with s5cmd
        select["completed"].append(subdir) 
        write(select) 
        continue

    print(f"{col.BOLD} {col.WARNING} {header} {col.OKCYAN} Failed to sync \"{relpath}\" with s5cmd. Retrying with aws-cli... {col.ENDC}")
    sys.stderr.write("S5CMD ERROR: " + abspath + "\n")
    awscli = os.system(f"aws s3 {cmd} {abspath} {bucket}/{relpath}")
    if os.waitstatus_to_exitcode(awscli) == 0:
        select["completed"].append(subdir) 
        write(select) 
        continue

    print(f"{col.BOLD} {col.FAIL} {header} Failed to sync \"{relpath}\" with awscli! {col.ENDC}")
    sys.stderr.write("AWSCLI ERROR: " + abspath + "\n")

    select["failed"].append(subdir) 
    write(select) 

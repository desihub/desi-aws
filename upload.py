import sys
import os
import json
from os import system, path
from datetime import datetime
import argparse

parser = argparse.ArgumentParser(
    prog='upload.py',
    description=
    """
Uploads stuff
    """
)
parser.add_argument('root', help='path to the root directory')
parser.add_argument('--bucket', help='URI to S3 bucket (s3://bucket)')
parser.add_argument('--selection', help='path to the list of selected nodes')
parser.add_argument('--max-dirs', type=int, help='maximum number of selected nodes to upload')
parser.add_argument('--max-workers', type=int, help='maximum number of workers to use')
args = parser.parse_args()

### FANCY COLORS

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

### TIMESTAMP

def timestamp():
    return f"[ {datetime.now().strftime('%H:%M:%S')} ]"

### INPUT FILE

## Load directory list
with open(args.selection) as f:
    select = json.load(f)

## Upload directories from queue
print(f"""
 {len(select["completed"]) + len(select["queued"])} {col.OKBLUE}directories listed for upload{col.ENDC}
 - {len(select["completed"])} {col.OKBLUE}already completed{col.ENDC}
 - {len(select["queued"])} {col.OKBLUE}queued (including {len(select["failed"])} previously failed){col.ENDC}
""")

## Max number of directories to upload; Default 8
try:
    max_dirs = int(sys.argv[2])
except Exception:
    max_dirs = 8
print(f"{col.OKGREEN} Uploading a maximum of {args.max_dirs} directories in this run {col.ENDC}")

print(f"{col.OKGREEN} Using a maximum of {args.max_workers} workers {col.ENDC}")

### OUTPUT FILE

## For updating directory list
def write(data):
    with open("select.json", "w") as f:
        json.dump(data, f)

### UPLOADS

index = 0
while len(select["queued"]) > 0:

    ## Stop if max_dirs exceeded
    if index == args.max_dirs: 
        print(f"{timestamp()} {col.OKBLUE}Finished uploading {args.max_dirs} directories. Stopping... {col.ENDC}")
        break

    subdir = select["queued"][0]
    index += 1

    ## Progress fraction indicator
    header = f"[ {index}/{args.max_dirs} ]"

    ## Absolute and relative path to directory/file
    abspath = path.abspath(subdir)
    relpath = path.relpath(abspath, args.root)

    ## Directory or file? 
    ## They have different upload commands, and directory path names need to terminate with /
    isdir = path.isdir(abspath)
    if isdir:
        abspath += "/"
        relpath += "/"
        cmd = "sync"
    else:
        cmd = "cp"

    ### ATTEMPT 1: S5CMD

    print(f"{timestamp()} {col.BOLD}{col.OKGREEN}{header}{col.OKCYAN} Syncing \"{relpath}\" with s5cmd... {col.ENDC}")

    s5cmd = os.system(f"s5cmd --numworkers {args.max_workers} --log error --stat {cmd} {abspath} {args.bucket}/{relpath}")
    
    ## Remove from queue if success
    if os.waitstatus_to_exitcode(s5cmd) == 0:
        select["queued"].remove(subdir) 
        if subdir in select["failed"]: select["failed"].remove(subdir) 
        select["completed"].append(subdir) 
        write(select) 
        continue

    ## Retry with aws-cli if fail
    print(f"{timestamp()} {col.BOLD}{col.WARNING}{header}{col.OKCYAN} Failed to sync \"{relpath}\" with s5cmd. Retrying with aws-cli... {col.ENDC}")
    sys.stderr.write("S5CMD ERROR: " + abspath + "\n")

    ### ATTEMPT 2: AWSCLI

    awscli = os.system(f"aws s3 {cmd} {abspath} {args.bucket}/{relpath}")

    ## Remove from queue if success
    if os.waitstatus_to_exitcode(awscli) == 0:
        select["queued"].remove(subdir) 
        if subdir in select["failed"]: select["failed"].remove(subdir) 
        select["completed"].append(subdir) 
        write(select) 
        continue

    ## If failed again, move to end of queue and append to failed list
    print(f"{timestamp()} {col.BOLD}{col.FAIL}{header} Failed to sync \"{relpath}\" with awscli! {col.ENDC}")
    sys.stderr.write("AWSCLI ERROR: " + abspath + "\n")

    select["queued"].remove(subdir) 
    select["failed"].append(subdir) 
    select["queued"].append(subdir) 
    write(select) 

print(f"""
 {len(select["completed"]) + len(select["queued"])} {col.OKBLUE}directories listed for upload{col.ENDC}
 - {len(select["completed"])} {col.OKBLUE}now completed{col.ENDC}
 - {len(select["queued"])} {col.OKBLUE}still queued (including {len(select["failed"])} failed){col.ENDC}
""")

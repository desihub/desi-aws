import sys
import os
import json
from os import system, path
from datetime import datetime
import argparse

## Command-line argument parsing

parser = argparse.ArgumentParser(
    prog='upload.py',
    description=
    """
Uploads stuff
    """
)
parser.add_argument('root', help='Path to the root directory')
parser.add_argument('--bucket', help='URI to S3 bucket (s3://bucket)')
parser.add_argument('--queue', help='Path to the list of queueed nodes')
parser.add_argument('--remap', help=
"""JSON key-value pairs specifying how specific directories are to be remapped to different targets.

{ "original_directory_1": "target_directory_1", "original_directory_2": "target_directory_2" } """)
parser.add_argument('--max-dirs', type=int, help='Maximum number of queueed nodes to upload')
parser.add_argument('--max-workers', type=int, help='Maximum number of workers to use')
args = parser.parse_args() # parse general args
args.remap = json.loads(args.remap) # parse the JSON

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
with open(args.batch) as f:
    queue = json.load(f)

## Upload directories from queue
print(f"""
 {len(queue["completed"]) + len(queue["queued"])} {col.OKBLUE}directories listed for upload{col.ENDC}
 - {len(queue["completed"])} {col.OKBLUE}already completed{col.ENDC}
 - {len(queue["queued"])} {col.OKBLUE}queued (including {len(queue["failed"])} previously failed){col.ENDC}
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
    with open(args.batch, "w") as f:
        json.dump(data, f)

### UPLOADS

index = 0
while len(queue["queued"]) > 0:

    ## Stop if max_dirs exceeded
    if index == args.max_dirs: 
        print(f"{timestamp()} {col.OKBLUE}Finished uploading {args.max_dirs} directories. Stopping... {col.ENDC}")
        break

    subdir = queue["queued"][0]
    index += 1

    ## Progress fraction indicator
    header = f"[ {index}/{args.max_dirs} ]"

    ## Given absolute path to directory/file, find target path

    abs_path = path.abspath(subdir)

    local_root = args.root
    target_root = args.bucket
    for key in args.remap:
        remap_local_root = path.join(local_root, key)
        remap_target_root = path.join(target_root, args.remap[key])
        if abs_path.startswith(remap_local_root):
            local_root = remap_local_root
            target_root = remap_target_root
            break

    rel_path = path.relpath(abs_path, local_root)

    local_path = str(abs_path)
    target_path = str(path.join(target_root, rel_path))

    ## Directory or file? 
    ## They have different upload commands, and directory path names need to terminate with /
    isdir = path.isdir(abs_path)
    if isdir:
        local_path += "/"
        target_path += "/"
        cmd = "sync"
    else:
        cmd = "cp"

    ### ATTEMPT 1: S5CMD

    print(f"{timestamp()} {col.BOLD}{col.OKGREEN}{header}{col.OKCYAN} Syncing \"{local_path}\" -> \"{target_path}\" with s5cmd... {col.ENDC}")

    s5cmd = os.system(f"s5cmd --numworkers {args.max_workers} --log error --stat {cmd} {local_path} {target_path}")
    
    ## Remove from queue if success
    if os.waitstatus_to_exitcode(s5cmd) == 0:
        queue["queued"].remove(subdir) 
        if subdir in queue["failed"]: queue["failed"].remove(subdir) 
        queue["completed"].append(subdir) 
        write(queue) 
        continue

    ## Retry with aws-cli if fail
    print(f"{timestamp()} {col.BOLD}{col.WARNING}{header}{col.OKCYAN} Failed to sync with s5cmd. Retrying with aws-cli... {col.ENDC}")
    sys.stderr.write("S5CMD ERROR: " + abs_path + "\n")

    ### ATTEMPT 2: AWSCLI

    awscli = os.system(f"aws s3 {cmd} {local_path} {target_path}")

    ## Remove from queue if success
    if os.waitstatus_to_exitcode(awscli) == 0:
        queue["queued"].remove(subdir) 
        if subdir in queue["failed"]: queue["failed"].remove(subdir) 
        queue["completed"].append(subdir) 
        write(queue) 
        continue

    ## If failed again, move to end of queue and append to failed list
    print(f"{timestamp()} {col.BOLD}{col.FAIL}{header} Failed to sync with awscli! {col.ENDC}")
    sys.stderr.write("AWSCLI ERROR: " + abs_path + "\n")

    queue["queued"].remove(subdir) 
    queue["failed"].append(subdir) 
    queue["queued"].append(subdir) 
    write(queue) 

print(f"""
 {len(queue["completed"]) + len(queue["queued"])} {col.OKBLUE}directories listed for upload{col.ENDC}
 - {len(queue["completed"])} {col.OKBLUE}now completed{col.ENDC}
 - {len(queue["queued"])} {col.OKBLUE}still queued (including {len(queue["failed"])} failed){col.ENDC}
""")

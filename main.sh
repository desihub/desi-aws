#!/usr/bin/env bash

## URI of S3 bucket
bucket="s3://desiproto"

### About the script
### ----------------

cmd="main.sh"

## If no input given, then print script description.
if [[ -z $1 ]]; then
    echo ""
    echo "(Expected one argument but got none. Printing script description.)"
    echo ""
    echo "$cmd"
    echo "    Uploads a data release directory to the bucket $bucket, chunking some large directories."
    echo "    Treats the root of the bucket as \$DESI_ROOT=$DESI_ROOT."
    echo "Usage: bash ./$cmd <path>"
    echo "    <path>: Absolute path to the data release directory"
    echo ""
    exit 0
fi

## Required for every unsanitized path because the S3 SDK does not treat multiple // as one /
## ${path%/} truncates a trailing / 
## ${path#/} truncates a leading /
absdir="${1%/}"

## This path is relative to both the NERSC and S3 roots
## ${path/#$DESI_ROOT} truncates a leading $DESI_ROOT/
reldir="${absdir#$DESI_ROOT/}"

## Cap number of directories uploaded
i=0
MAX_DIRS=1
## Chunk in depth of 3 (enough to chunk $DESI_ROOT/$reldir/spectro/data into per-night uploads)
for subdir in $DESI_ROOT/$reldir/*/*/*/; do
    abssubdir="${subdir%/}"
    relsubdir="${abssubdir#$DESI_ROOT/$reldir/}"
    echo "[$cmd : Info] bash ./upload.sh $abssubdir"
    # bash ./upload.sh "$abssubdir"
    i=$(($i+1))
    if [[ $i -eq $MAX_DIRS ]]; then
        echo "[$cmd : Warning] \$MAX_DIRS exceeded. Stopping."
        break
    fi
done


echo "[$cmd : Info] Done!"

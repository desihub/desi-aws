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

## (Debug) Cap number of directories uploaded
maxdirs=8
if [[ $maxdirs -ge 0 ]]; then
    echo "[$cmd : WARNING] Debug flag \$maxdirs==$maxdirs is positive. Total number of uploads is capped."
    break
fi

## Upload directory in chunks
## Chunk in depth of 3 (enough to chunk $DESI_ROOT/$reldir/spectro/data into per-night uploads)
numdirs=$(echo $DESI_ROOT/$reldir/*/*/*/ | wc -w)
echo "[$cmd: Info] Found $numdirs subdirectories at depth 3 from $DESI_ROOT/$reldir"
i=0
for subdir in $DESI_ROOT/$reldir/*/*/*/; do
    i=$(($i+1))
    abssubdir="${subdir%/}"
    relsubdir="${abssubdir#$DESI_ROOT/$reldir/}"
    echo "[$cmd : Info] [$i/$numdirs] bash ./upload.sh $abssubdir"
    bash ./upload.sh "$abssubdir"
    if [[ $i -eq $maxdirs ]]; then
        echo "[$cmd : Info] \$maxdirs==$maxdirs exceeded. Stopping."
        break
    fi
done


echo "[$cmd : Info] Done!"

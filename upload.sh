#!/usr/bin/env bash

## URI of S3 bucket
bucket="s3://desiproto"

### About the script
### ----------------

cmd="upload.sh"

## If no input given, then print script description.
if [[ -z $1 ]]; then
    echo ""
    echo "(Expected one argument but got none. Printing script description.)"
    echo ""
    echo "$cmd"
    echo "    Uploads a directory to the bucket $bucket"
    echo "    Treats the root of the bucket as \$DESI_ROOT=$DESI_ROOT"
    echo "Usage: bash ./$cmd <path>"
    echo "    <path>: Absolute path to the directory"
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

### Debug flags
### -----------

simerr=1
cleanup=1
if [[ $simerr -eq "1" ]]; then
	echo "[$cmd : WARNING] Debug flag simerr==1. Will insert a dummy error during s5cmd sync."
fi
if [[ $cleanup -eq "1" ]]; then
	echo "[$cmd : WARNING] Debug flag cleanup==1. Will delete all files uploaded during this session before exiting."
fi

### Logging
### -------

timestamp=$(date +%s)
logdir="upload_logs"
mkdir -p "$logdir/$timestamp"
sync_log="$logdir/$timestamp/sync.txt"
retry_log="$logdir/$timestamp/retry.txt"
echo "[$cmd : Info] $sync_log $retry_log"

### Sync with S5cmd
### ---------------

from="$DESI_ROOT/$reldir"
to="$bucket/$reldir"
echo "[$cmd : Info] s5cmd sync $from/ $to/"
s5cmd sync "$from/" "$to/" 2>> "$sync_log"

### (Debug) Simulate sync error
### ---------------------------

if [[ $simerr -eq "1" ]]
then
	echo "[$cmd : Debug] Simulating sync error"
	echo 'ERROR "cp /global/cfs/cdirs/desi/public/edr/spectro/data/20201025/00062169/fvc-00062169.fits.fz s3://desiproto/public/edr/spectro/data/20201025/00062169/fvc-00062169.fits.fz": InvalidDigest: The Content-MD5 you specified was invalid. status code: 400, request id: S3TR4P2E0A2K3JMH7, host id: XTeMYKd2KECOHWk5S' > "$sync_log"
fi

### Retry failures with aws-cli
### ---------------------------

regex_from='(?<="cp\s).*?(?=\s)' # matches origin file
regex_to='(?<=\s)s3://.*?(?=")' # matches destination file
while read line; do
	line_from=$(echo "$line" | grep -P -o $regex_from)
	line_to=$(echo "$line" | grep -P -o $regex_to)
	if [[ -n $from ]]; then
		echo "[$cmd : Info] aws s3 cp $line_from $line_to"
		aws s3 cp "$line_from" "$line_to" 2>> "$retry_log"
	fi
done <"$sync_log"

### (Debug) Delete uploaded objects
### -------------------------------

if [[ $cleanup -eq "1" ]]
then
	echo "[$cmd : Debug] Deleting uploaded objects"
	s5cmd rm "$to/*"
fi

echo "[$cmd : Info] Done!"

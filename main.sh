#!/usr/bin/env bash

#DESI_ROOT="$HOME/docs/desi/desispec" ## debug

debug=1
if [[ $debug -eq "1" ]]
then
	echo "[Debug] Debug flag is set to 1. Will delete after upload"
fi

### Path to the released directory relative to $DESI_ROOT. Make sure it ends with /

#release="public/edr"
release="public/edr/spectro/data/20201025/"
#release="doc/" ## debug

### Setup error logs

timestamp=$(date +%s)
mkdir "upload_$timestamp"
sync_log="upload_$timestamp/sync.txt"
retry_log="upload_$timestamp/retry.txt"
echo "[Logs] $sync_log $retry_log"

### Sync with S5cmd

from="$DESI_ROOT/$release"
to="s3://desiproto/$release"
echo "[Sync] $from > $to"
s5cmd sync "$from" "$to" 2>> "$sync_log"

### (Debug) Simulate sync error

if [[ $debug -eq "1" ]]
then
	echo "[Debug] Simulating sync error"
	echo 'ERROR "cp /global/cfs/cdirs/desi/public/edr/spectro/data/20201025/00062169/fvc-00062169.fits.fz s3://desiproto/public/edr/spectro/data/20201025/00062169/fvc-00062169.fits.fz": InvalidDigest: The Content-MD5 you specified was invalid. status code: 400, request id: S3TR4P2E0A2K3JMH7, host id: XTeMYKd2KECOHWk5S' > "$sync_log"
fi

### Read error logs and retry any bad files with aws cli

regex_from='(?<="cp\s).*?(?=\s)' # matches origin file
regex_to='(?<=\s)s3://.*?(?=")' # matches destination file
while read line; do
	line_from=$(echo "$line" | grep -P -o $regex_from)
	line_to=$(echo "$line" | grep -P -o $regex_to)
	if [[ -n $from ]]; then
		echo "[Retry] $line_from >> $line_to"
		aws s3 cp "$line_from" "$line_to" 2>> "$retry_log"
	fi
done <"$sync_log"

### (Debug) Delete uploaded objects

if [[ $debug -eq "1" ]]
then
	echo "[Debug] Deleting uploaded objects"
	s5cmd rm "$to*"
fi

echo "[Done]"

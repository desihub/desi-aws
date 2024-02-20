#!/usr/bin/env bash

regex_from='(?<="cp\s).*?(?=\s)' # matches origin file
regex_to='(?<=\s)s3://.*?(?=")' # matches destination file
while read line; do
	from=$(echo "$line" | grep -P -o $regex_from)
	to=$(echo "$line" | grep -P -o $regex_to)
	if [[ -n $from ]]; then
		echo "--RETRYING $from"
		echo "--to $to"
	fi
done <err-sync.txt


#!/usr/bin/env bash

N=1 # number of directories to test
i=0 # iterator

for dir in $DESI_ROOT/spectro/data/*/
do
	i=$((i+1))
	echo "--TEST $i: $dir"
	echo "--UPLOAD"
	s5cmd sync "$dir" "s3://desiproto/s5cmd/$dir" 2>> err-sync.txt
	echo "--DELETE"
	s5cmd rm "s3://desiproto/s5cmd/$dir*" 2>> err-rm.txt

	if [ $i == $N ]
	then
		break
	fi
done
# time aws s3 sync "$DESI_ROOT/spectro/data/20200508/" "s3://desiproto/awscli/spectro/data/20200508/"
# time s5cmd sync "$DESI_ROOT/spectro/data/20200508/" "s3://desiproto/s5cmd/spectro/data/20200508/"

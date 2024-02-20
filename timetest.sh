#!/usr/bin/env bash
time aws s3 sync "$DESI_ROOT/spectro/data/20200508/" "s3://desiproto/awscli/spectro/data/20200508/"
time s5cmd sync "$DESI_ROOT/spectro/data/20200508/" "s3://desiproto/s5cmd/spectro/data/20200508/"

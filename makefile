# Base directory in S3 bucket
root=$(DESI_ROOT)/public

# Specific data release
release=$(root)/edr/spectro/redux/fuji

# Subdirectory that we want to upload
subdir=$(release)

# Find: Scan for filesystem structure in the release
find.json: find.py
	python3 find.py $(release) -o $@

# Batch: Batch upload paths into large directories (>10^12 bytes), and add these to the queue
batch.json: batch.py find.json
	python3 batch.py $(release) --file-tree find.json --subdir $(subdir) --max-batch-size 1000000000000 -o $@

# Upload: Upload batch directories
upload: upload.py queue.json
	python3 upload.py $(root) \
		--bucket s3://desidata \
		--batch batch.json \
		--remap '{ "$(release)/spectro/data": "raw_spectro_data", "$(release)/target": "target" }' \
		--max-dirs 100 \
		--max-workers 128 \
		2> upload_errors.txt

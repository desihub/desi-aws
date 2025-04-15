# Root directory to public DESI files
# change `dvs_ro` to `global` for write access
DESI_ROOT ?= =/dvs_ro/cfs/cdirs/desi/public

DESI_RELEASE ?= DR1

# Specific data release
release=$(DESI_ROOT)/$(DESI_RELEASE)

# Subdirectory that we want to upload
DESI_RELEASE_SUBDIR ?= $(release)

# Find: Scan for filesystem structure in the release
find.json: find.py makefile
	python3 find.py $(release) --max-workers 128 --log-depth 2 -o $@

# Batch: Batch upload paths into large directories (>10^12 bytes), and add these to the queue
batch.json: batch.py find.json makefile
	python3 batch.py $(release) --file-tree find.json --subdir $(DESI_RELEASE_SUBDIR) --max-batch-size 1000000000000 -o $@

# Upload: Upload batch directories
upload: upload.py queue.json makefile
	python3 upload.py $(DESI_ROOT) \
		--bucket s3://desidata \
		--batch batch.json \
		--remap '{ "$(release)/spectro/data": "raw_spectro_data", "$(release)/target": "target" }' \
		--max-dirs 1000 \
		--max-workers 64 \
		2> upload_errors.txt

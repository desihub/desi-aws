# Base directory in S3 bucket
root=$(DESI_ROOT)/public

# Specific data release
release=$(root)/edr

# Subdirectory that we want to upload
select=$(release)

# Build scanning program
find: find.cpp
	g++ find.cpp -std=c++20 -lboost_program_options -o $@

# Find: Scan for filesystem structure in the release
find.json: find
	./find $(release) > $@

# Select: Batch upload paths into large directories (>10^12 bytes)
select.json: select.py find.json
	python3 select.py $(release) --file-tree find.json --selection $(select) --min-size 1000000000000 -o $@

# Upload: Upload batch directories
upload: upload.py select.json
	python3 upload.py $(root) \
		--bucket s3://desiproto \
		--selection select.json \
		--remap '{ "$(release)/spectro/data": "raw_spectro_data", "$(release)/target": "target" }' \
		--max-dirs 100 \
		--max-workers 128 \
		2> upload_errors.txt

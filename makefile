# Base directory in S3 bucket
root=$(DESI_ROOT)/public

# Specific data release
release=$(root)/edr

# Subdirectory that we want to upload
select=$(release)

find: find.cpp
	g++ find.cpp -std=c++20 -lboost_program_options -o $@

find.json: find
	./find $(release) > $@

select.json: select.py find.json
	python3 select.py $(release) --file-tree find.json --selection $(select) --min-size 1000000000000 -o $@

upload: upload.py select.json
	python3 upload.py $(root) \
		--bucket s3://desiproto \
		--selection select.json \
		--max-dirs 100 \
		--max-workers 128 \
		2> upload_errors.txt

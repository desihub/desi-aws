release=$(DESI_ROOT)/public/edr

find: find.cpp
	g++ find.cpp -std=c++20 -o find

find.json: find
	./find $(release) > find.json

select.json: select.py find.json
	python3 select.py $(release)

upload: upload.py select.json
	python3 upload.py $(release) 100 128 2> upload_errors.txt

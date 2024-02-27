release=$(DESI_ROOT)/public/edr

find:
	g++ find.cpp -std=c++20 -o find

find.json: find
	./find $(release) > find.json

select.txt: find.json
	python3 select.py $(release) > select.txt

upload: select.txt
	python3 upload.py $(release) 2> upload_errors.txt

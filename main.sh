release="$DESI_ROOT/public/edr"
make find
./find "$release" > find.json
python3 select.py "$release" > select.txt
python3 upload.py "$release" 2> upload_errors.txt

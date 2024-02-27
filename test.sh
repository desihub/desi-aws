release="$DESI_ROOT/public/edr/spectro/data/20200211"

make find

echo "Finding directories..."
./find "$release" > find.json

echo "Selecting large directories..."
python3 select.py "$release" 3 > select.txt

echo "Uploading large directories..."
python3 upload.py "$release" 2> upload_errors.txt

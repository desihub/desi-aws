# DESI mirror on AWS S3

Tooling for uploading DESI data from NERSC Perlmutter to AWS S3.

## Usage

The upload configuration is set in the *makefile*.
When uploading a new release, you ideally only need to change the `release` variable in the *makefile* (from, say `$(root)/edr` to `$(root)/dr1`),
then run
```bash
make upload
```
in a login node repeatedly until all files have been transferred.
However, my code could very well break in a year or two, so below are all the details.

### Paths to main directories

The **root directory** at the AWS S3 bucket corresponds to NERSC's parent directory for DESI public releases.
It contains the **release directories** `edr`\[, `dr1`, `dr2`, and `dr3`\]<sup>(planned)</sup>, which correspond to the releases directly,
as well as the **common data directories** `raw_spectro_data` and `target`, which correspond to data shared across the releases.

We specify the relations between the **root directory** and the **release directories** with the following variables at the top of the *makefile*:

* `root`: The directory at Perlmutter corresponding to the root directory in the S3 bucket.
  * In general, this should be the read-only path `/dvs_ro/cfs/cdirs/desi/public`. If you run into file permission errors, try changing from `/dvs_ro` to `/global`.
* `release`: The directory at Perlmutter correspoding to a specific DESI data release.
  * Example values are `$(root)/edr`, `$(root)/dr1`, `$(root)/dr2`, ...
* `subdir`: The directory at Perlmutter corresponding to a subdirectory of the release you want to select for upload.
  * In general, this should be the full release path `$(release)`. You should only change this to a subdirectory (e.g. `$(release)/spectro/redux`) for testing.

Note that the **common data directories** are configured later, in the upload section in the *makefile*.

### Crawling the filesystem

Before we can upload the specified **release directory**, 
we need to determine the structure and storage sizes of its subdirectories and files
as to 1) make sure we aren't missing anything and 2) be able to batch our uploads into smaller chunks for easier oversight.
This is done by running
```bash
make find.json
```
which uses the *find.py* script to generate a JSON file tree stored as *find.json*.

The *find.py* script is a multi-threaded, recursive filesystem crawler. For example, given a directory structure like
```
.
├── docs
│   ├── entry_schema.png
│   └── README.md
├── batch.json
├── batch.py
├── find.json
├── find.py
├── LICENSE
├── makefile
└── upload.py
```
it generates a JSON tree like
```json
[
  ".", 0, 89110240,
  [ "docs", 0, 28915,
    [ "README.md", 1, 478 ],
    [ "entry_schema.png", 1, 28437 ]
  ],
  [ "LICENSE", 1, 1495 ],
  [ "batch.json", 1, 309506 ],
  [ "batch.py", 1, 2964 ],
  [ "find.json", 1, 88754948 ],
  [ "find.py", 1, 6271 ],
  [ "makefile", 1, 925 ],
  [ "upload.py", 1, 5216 ]
]
```
Each array is a node in the JSON tree. Its elements are
* Index 0: the name of the file or directory.
* Index 1: the node type (0 for directory, 1 for file).
* Index 2: the node size, in bytes. For a directory, this is the recursive sum of its children's sizes.
* The remaining elements are the node's child nodes. They have the same structure.

More details can be found in the inline comments of *find.py*, or by running
```bash
python3 find.py --help
```

### Batching

We upload in batches of approximately 10 gigabytes to 1 terabyte in size each to allow for easy monitoring, stopping, and restarting during the upload.
This means each release has a few thousand to tens of thousands of batches, each taking a few seconds to a few minutes to upload.
To generate these batches, we run
```
make batch.json
```
which looks for satisfactory directories and files with *batch.py*, storing them in *batch.json*.

### Upload

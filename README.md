# DESI mirror on AWS S3

Tooling for uploading DESI data from NERSC Perlmutter to AWS S3.

## Installation

First, ensure you have the following dependencies installed/satisfied:
1. An AWS user account with read and write access to the **desidata** storage bucket. Contact Anthony Kremin or Stephen Bailey for this.
2. **Python 3**.
3. **aws-cli**, AWS's official command-line client. Refer to the instructions at [docs.aws.amazon.com/AmazonS3/latest/userguide/setup-aws-cli.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/setup-aws-cli.html) to install and configure with your AWS credentials.
4. **s5cmd**, the third-party S3 upload client we use. Refer to the instructions at [github.com/peak/s5cmd](https://github.com/peak/s5cmd).

Then, clone this repository into your space at NERSC Perlmutter.

## Simple usage

The upload configuration is set in the *makefile*.
When uploading a new release, you ideally only need to change the `release` variable in the *makefile* (from, say `$(root)/edr` to `$(root)/dr1`),
then run
```bash
make upload
```
in a login node repeatedly until all files have been transferred.
However, my code could very well break in a year or two, so below is a full explanation of the pipeline.

## Advanced configuration

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

The *find.py* script is a multi-threaded filesystem crawler. 
Its performance is bounded by the speed of calls to the operating system,
so it runs best with a large number of workers available in its thread pool.
Thus, the `--max-workers` parameter in the *makefile* should be set anywhere between 32 and 128,
and and you should run `make find.json` in a **compute node** with the corresponding number of CPUs.

---
<details>
 <summary><h4>Technical details</h4></summary>

The *find.py* script recursively crawls the filesystem starting from a specified root directory.
It outputs a JSON tree of every file and subdirectory contained within a specified depth (default: unlimited),
with information on their name, type, and byte size.
For example, if the given root directory has the following structure,
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
  [
    "docs", 0, 28915,
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
</details>

---

### Batching

We upload in batches of approximately 10 gigabytes to 1 terabyte in size each to allow for easy monitoring, stopping, and restarting during the upload.
This means each release has a few thousand to tens of thousands of batches, each taking a few seconds to a few minutes to upload.
To generate these batches, we run
```
make batch.json
```
which looks for satisfactory directories and files with *batch.py*, storing them in *batch.json*. 
This script is very fast, so it can be run in the **login node**.

For testing, you may filter the selection to only within a specific subdirectory of the root directory by setting the `subdir` variable in the *makefile*.

---
<details>
 <summary><h4>Technical details</h4></summary>
</details>

---

### Upload

To upload, run
```
make upload
```
repeatedly until every batch has been transferred.
This calls the *upload.py* script. By default, 1000 batches are transferred in each run. 
Feel free to adjust this `--max-batches` parameter depending on how often you want the script to automatically stop.

This script is best run in a **login node**, which has much faster network connections than a **compute node**. 


```
make upload
```
The number of batches to run until the program (*upload.py*) exits can be configured in the *makefile* with *--max-dirs*. 
The default is 1000, and we recommend something in that magnitude for an overnight upload.

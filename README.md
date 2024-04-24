# DESI mirror on AWS S3

Tooling for uploading DESI data from NERSC Perlmutter to AWS S3.

Configuration is set in the **makefile**.
* `root`: The directory at Perlmutter corresponding to the root directory in the S3 bucket.
* `release`: The directory at Perlmutter correspoding to a specific DESI data release.
* `select`: The directory at Perlmutter corresponding to a subdirectory of the release
  (or if uploading the full release at once, then just the release directory).

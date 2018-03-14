# gcp-scripts
Miscellaneous GCP scripts

## gcp-ssh-key-adder.py

Quickly and easily add local SSH keys to your project's metadata with this
handy-dandy script! Simply invoke the script with a path to one or more public
SSH keys, and let the script do the rest!

Requires Python 3, and PyYAML. Wraps `gcloud` commands, so ensure that works!

```
usage: gcp-ssh-key-adder.py [-h] [-i] [-d]
                            public-ssh-key-file [public-ssh-key-file ...]

Add SSH keys to Google Cloud, the easy way!

positional arguments:
  public-ssh-key-file  path to public SSH key file you wish to add

optional arguments:
  -h, --help           show this help message and exit
  -i, --info           enable info logging mode
  -d, --debug          enable debug logging mode

A tdg script.
```

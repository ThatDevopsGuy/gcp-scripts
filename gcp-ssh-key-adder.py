#!/usr/bin/env python3
# gcp-ssh-key-adder.py
# Adds ssh-keys to GCP the easy way
# 2018, Sebastian Weigand || tdg@google.com
# Version 1.0

import subprocess
import yaml
import argparse
import os
import sys
import tempfile
import logging

# =============================================================================
# Initialization
# =============================================================================

parser = argparse.ArgumentParser(
    description='Add SSH keys to Google Cloud, the easy way!',
    epilog='A tdg script.')

parser.add_argument(
    'ssh_key_files',
    metavar='public-ssh-key-file',
    nargs='+',
    help='path to public SSH key file you wish to add')

parser.add_argument(
    '-i',
    '--info',
    action="store_true",
    default=False,
    help='enable info logging mode')

parser.add_argument(
    '-d',
    '--debug',
    action="store_true",
    default=False,
    help='enable debug logging mode')

args = parser.parse_args()

logger = logging.getLogger('gcp-ssh-key-adder')
logger.setLevel(logging.WARN)

formatter = logging.Formatter('[%(asctime)s] | %(levelname)-8s | %(message)s')

console = logging.StreamHandler()
console.setLevel(logging.WARN)
console.setFormatter(formatter)

logger.addHandler(console)

if args.info:
    logger.setLevel(logging.INFO)
    console.setLevel(logging.INFO)

if args.debug:
    logger.setLevel(logging.DEBUG)
    console.setLevel(logging.DEBUG)

# =============================================================================
# Helper functions
# =============================================================================


def eprint(*text):
    print(*text, file=sys.stderr)


# =============================================================================
# New Key Parsing
# =============================================================================

# Path cleaning for multiple SSH keys:
ssh_key_file_paths = [
    os.path.expanduser(os.path.realpath(path)) for path in args.ssh_key_files
]

# Path sanity:
logger.info('Checking SSH paths for existence and readability...')
for path in ssh_key_file_paths:
    logger.debug('Processing: %s' % path)
    if not os.path.exists(path):
        exit('Could not read path: %s' % path)

    if not os.access(path, os.R_OK):
        exit('Insufficient privilegs to read path: %s' % path)

# Process new keys:
keys_ok = True
ssh_keys = []

logger.info('Reading in SSH keys from paths...')
for path in ssh_key_file_paths:
    logger.debug('Processing: %s' % path)
    with open(path, 'r') as f:
        _ssh_key = f.read()

        try:
            _key_type, _key, _userhost = _ssh_key.split()
            _user = _userhost.split('@')[0]

            _new_key = '{user}:{key_type} {key} {userhost}'.format(
                user=_user, key_type=_key_type, key=_key, userhost=_userhost)
            ssh_keys.append(_new_key)

        except ValueError as e:
            eprint(
                'Invalid SSH key format (expecting <key_type> <key> <user@host> per line): ',
                _ssh_key)
            keys_ok = False

if not keys_ok:
    exit('Errors encountered while parsing SSH keys, so aborting.')

# =============================================================================
# Old Key Parsing
# =============================================================================

# Get current SSH keys:
metadata_command = subprocess.run(
    ['gcloud', 'compute', 'project-info', 'describe'], stdout=subprocess.PIPE)

if metadata_command.returncode != 0:
    exit('gcloud command invocation error')

logger.debug('Parsing YAML from gcloud command...')
metadata = yaml.load(metadata_command.stdout)

logger.debug('Reading keys from parsed YAML...')
for key in metadata['commonInstanceMetadata']['items']:
    if key['key'] == 'ssh-keys':
        ssh_keys += key['value'].splitlines()
        break

# =============================================================================
# File Generation
# =============================================================================

# File creation:
fd, tempfile_path = tempfile.mkstemp()
logger.debug('Created temporary file: %s' % tempfile_path)

logger.debug('Note: Will not write exact duplicate keys...')
with open(tempfile_path, 'w') as f:
    for ssh_key in set(ssh_keys):
        f.write(ssh_key)
        f.write('\n')

os.close(fd)

logger.debug('Wrote and closed temporary file.')

# =============================================================================
# Invocation
# =============================================================================

print('Updating keys in Google Cloud (this may take a few moments)...')

update_command = subprocess.run(
    [
        'gcloud', 'compute', 'project-info', 'add-metadata',
        '--metadata-from-file', 'ssh-keys=' + tempfile_path
    ],
    stdout=subprocess.PIPE)

if metadata_command.returncode != 0:
    exit('gcloud command invocation error')

os.remove(tempfile_path)
logger.debug('Removed temporary file.')

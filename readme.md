# Git Lock Notifier

This is a simple script that periodically checks for differences in locked files in a local repository with LFS.

## Installation

1. Install Python 3.9
2. Install Pipenv
3. Run `pipenv install` to create a virtual environment and install the required packages
4. Create a `env-load.sh` file to setup environment variables (see below)

### env-load.sh

Example `env-load.sh` file:

```bash
#!/bin/sh

export REPO_DIR="YOUR-REPO-DIR"
export WEBHOOK_URL="YOUR-DISCORD-WEBHOOK-URL"

python lfs_checker.py
```

## Usage

Just run `pipenv run withenv`

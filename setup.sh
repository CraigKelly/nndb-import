#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR

echo -e "\033[32mStarting setup in $(pwd)...\033[0m"

if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "\033[33mWARNING: virtual env already there - skipping setup\033[0m"
else
    echo -e "\033[33mSetting up virtualenv in venv\033[0m"
    virtualenv -p python3 venv
fi

source $SCRIPT_DIR/venv/bin/activate
echo "Using this python: $(which python)"

echo -e "\033[33mUsing latest setuptools pip wheel\033[0m"
pip install --upgrade setuptools pip wheel

echo -e "\033[33mInstalling reqs in $SCRIPT_DIR/requirements.txt\033[0m"
pip install --upgrade -r "$SCRIPT_DIR/requirements.txt"

echo -e "\033[32mSetup Complete\033[0m"

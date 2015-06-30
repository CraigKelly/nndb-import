#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR

source $SCRIPT_DIR/venv/bin/activate
./nndb_import.py $*

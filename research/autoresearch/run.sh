#!/bin/zsh
cd ~/coffee_project/autoresearch && source ../venv/bin/activate
export DYLD_LIBRARY_PATH="$PWD/../venv/lib/python3.12/site-packages/sklearn/.dylibs" PYTHONWARNINGS=ignore OMP_NUM_THREADS=1
python "$@"

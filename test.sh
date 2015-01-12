#!/bin/bash

set -e

counter=1

cleanup(){
    echo "=== test $counter ==="
    if [[ -n $VIRTUAL_ENV ]]; then
	deactivate
    fi
    rm -rf wheelstreet test-env
    unset WHEELSTREET
    counter=$((counter+1))
}

exists(){
    test -e "$1" || (echo "error: $1 not found"; exit 1)
}

quiet="-q"
verbose=""

cleanup
./mkvenv.py $quiet $verbose virtualenv test-env
exists test-env

cleanup
./mkvenv.py $quiet $verbose --wheelstreet wheelstreet wheel
exists wheelstreet

cleanup
WHEELSTREET=wheelstreet ./mkvenv.py $quiet $verbose wheel
exists wheelstreet

cleanup
./mkvenv.py $quiet $verbose --wheelstreet wheelstreet wheel --requirements requirements.txt

## install, wheel exists before installation
cleanup
export WHEELSTREET=wheelstreet
./mkvenv.py $quiet $verbose wheel -r requirements.txt
./mkvenv.py $quiet $verbose install -r requirements.txt --venv test-env
exists wheelstreet
exists test-env

## install, caching wheel in the process
cleanup
export WHEELSTREET=wheelstreet
./mkvenv.py $quiet $verbose wheel
./mkvenv.py $quiet $verbose install -r requirements.txt --venv test-env
exists wheelstreet
exists test-env

## installation without wheel
cleanup
./mkvenv.py $quiet $verbose install -r requirements.txt --venv test-env --no-cache
exists test-env

## installation to existing, active virtualenv
cleanup
./mkvenv.py $quiet $verbose virtualenv test-env
exists test-env
source test-env/bin/activate
./mkvenv.py $quiet $verbose install -r requirements.txt --no-cache
./mkvenv.py $quiet $verbose show --venv test-env flake8

cleanup

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

cleanup
./hoist.py virtualenv test-env
exists test-env

cleanup
./hoist.py --wheelstreet wheelstreet wheel
exists wheelstreet

cleanup
WHEELSTREET=wheelstreet ./hoist.py wheel
exists wheelstreet

cleanup
./hoist.py --wheelstreet wheelstreet wheel --requirements requirements.txt

## install, wheel exists before installation
cleanup
export WHEELSTREET=wheelstreet
./hoist.py wheel -r requirements.txt
./hoist.py install -r requirements.txt --venv test-env
exists wheelstreet
exists test-env

## install, caching wheel in the process
cleanup
export WHEELSTREET=wheelstreet
./hoist.py wheel
./hoist.py install -r requirements.txt --venv test-env
exists wheelstreet
exists test-env

## installation without wheel
cleanup
./hoist.py install -r requirements.txt --venv test-env --no-cache
exists test-env

## installation to existing, active virtualenv
cleanup
./hoist.py virtualenv test-env
exists test-env
source test-env/bin/activate
./hoist.py install -r requirements.txt --no-cache
./hoist.py show --venv test-env six

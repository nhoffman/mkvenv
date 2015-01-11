#!/bin/bash

set -e

cleanup(){
    rm -rf wheelstreet test-env
    unset WHEELSTREET
}

exists(){
    test -e "$1" || (echo "error: $1 not found"; exit 1)
}

# cleanup
# ./hoist.py virtualenv test-env
# exists test-env

# cleanup
# ./hoist.py --wheelstreet wheelstreet wheel
# exists wheelstreet

# cleanup
# WHEELSTREET=wheelstreet ./hoist.py wheel
# exists wheelstreet

# cleanup
# ./hoist.py --wheelstreet wheelstreet wheel --requirements requirements.txt

cleanup
export WHEELSTREET=wheelstreet
./hoist.py wheel --requirements requirements.txt
# ./hoist.py install -w wheelstreet -r requirements.txt --venv test-env
# exists wheelstreet
# exists test-env

# test installation without wheel
# cleanup
# WHEELSTREET=wheelstreet ./hoist.py install -r requirements.txt --venv test-env
# exists test-env


#!/bin/bash

set -e

# from virtualenv/bin/activate
deactivate () {
    unset pydoc

    # reset old environment variables
    if [ -n "$_OLD_VIRTUAL_PATH" ] ; then
        PATH="$_OLD_VIRTUAL_PATH"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    if [ -n "$_OLD_VIRTUAL_PYTHONHOME" ] ; then
        PYTHONHOME="$_OLD_VIRTUAL_PYTHONHOME"
        export PYTHONHOME
        unset _OLD_VIRTUAL_PYTHONHOME
    fi

    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
        hash -r 2>/dev/null
    fi

    if [ -n "$_OLD_VIRTUAL_PS1" ] ; then
        PS1="$_OLD_VIRTUAL_PS1"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    if [ ! "$1" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}

counter=1

cleanup(){
    echo "=== test $counter ==="
    # ensure that no virtualenv is active
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
./mkvenv.py $quiet $verbose --wheelstreet wheelstreet \
	    wheelhouse
exists wheelstreet

cleanup
WHEELSTREET=wheelstreet ./mkvenv.py $quiet $verbose wheelhouse
exists wheelstreet

cleanup
./mkvenv.py $quiet $verbose --wheelstreet wheelstreet wheelhouse \
	    --requirements requirements.txt

## install, wheel exists before installation
cleanup
export WHEELSTREET=wheelstreet
./mkvenv.py $quiet $verbose wheelhouse -r requirements.txt
./mkvenv.py $quiet $verbose install -r requirements.txt --venv test-env
exists wheelstreet
exists test-env

## install, caching wheel in the process
cleanup
export WHEELSTREET=wheelstreet
./mkvenv.py $quiet $verbose wheelhouse
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

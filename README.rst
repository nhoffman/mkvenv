======
mkvenv
======

A wrapper for virtualenv, pip, and wheel that caches wheels to speed
up virtualenv creation.

Features:

* Create and maintain a cache of wheels.
* Create a virtualenv and install packages from the wheel cache in a
  single command.
* Add to the wheel cache as new packages are built.
* Download the ``virtualenv`` source code when not already installed
  or out of date.

Note that this package should be considered alpha/unstable!

Requirements
============

* Python 2.7
* Unix-like systems (ie, not Windows)

Examples
========

Create a wheel cache (~/.mkvenv by default)::

  % mkvenv wheelstreet
  % mkvenv list-wheels
  # Wheels in /Users/nhoffman/.mkvenv/2.7.7/

Now create a new virtualenv named ``test-env`` and install some
packages. As each package is installed, a wheel is first built and
saved to the cache, along with wheels for any dependencies::

  % cat requirements.txt
  flake8
  % mkvenv install --venv test-env -r requirements.txt
  % test-env/bin/pip freeze
  flake8==2.3.0
  mccabe==0.3
  pep8==1.5.7
  pyflakes==0.8.1
  wsgiref==0.1.2
  % mkvenv list-wheels
  # Wheels in /Users/nhoffman/.mkvenv/2.7.7/ =
  flake8-2.3.0-py2.py3-none-any.whl
  mccabe-0.3-py2.py3-none-any.whl
  pep8-1.5.7-py2.py3-none-any.whl
  pyflakes-0.8.1-py2.py3-none-any.whl

Subsequent requests to install any of these packages will use the
cached wheels.

Installation from the wheel cache can speed things up a lot when
packages require compilation::

  % cat scientific.txt
  numpy
  scipy
  pandas
  biopython
  seqmagick
  % mkvenv install --venv sci-env -r scientific.txt
  620.66s user 36.41s system 75% cpu 14:28.52 total
  % mkvenv install --venv another-env -r scientific.txt
  10.87s user 4.82s system 18% cpu 1:24.65 total

Installation
============

Installation is most easily performed from PyPi using pip::

  pip install mkvenv

Alternatively, obtain the source code from either PyPi
(https://pypi.python.org/pypi/mkvenv) or GitHub
(https://github.com/nhoffman/mkvenv) and install by running either
``python setup.py install`` or ``pip install .`` from within the
package directory. Installation provides a script named ``mkvenv`` as
an entry point. ``mkvenv.py`` may also be executed directly from the
top level of the package directory.

Alternatively, note that the mkvenv script is implemented as a single
python file that can be invoked directly as a script. This script can
be downloaded and used to create a virtualenv on a system on which the
``virtualenv`` package is not available::

  wget https://raw.githubusercontent.com/nhoffman/mkvenv/master/mkvenv/mkvenv.py
  python mkvenv.py

It may also be useful to distribute ``mkvenv.py`` along with other
projects to facilitate creation of execution environments.

Execution
=========

Run ``mkvenv -h`` for a list of subcommands and common options, or
``mkvenv <subcommand> -h`` for help on a subcommand. Note that common
options must be provided before the name of the subcommand
(eg, ``mkvenv -v wheelstreet -r requirements.txt``)

Known Bugs
==========

There's a known bug in pip using python 2.7 on OS X
(https://github.com/pypa/pip/issues/1964 - the issue is not specific
to this project) that results in an error on installation from PyPI
with the message "AssertionError: Multiple .dist-info directories"
after a previous installation. The solution is to delete any residual
pip build directories::

  find /private -name 'mkvenv' -exec rm -r "{}" \; 2> /dev/null

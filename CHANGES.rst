====================
 Changes for mkvenv
====================

0.2.3
=====

* update minimum version of virtualenv to 13.1.0
* --no-cache allows pip to download packages from index
* `init --check` prints path of wheelhouse to stdout
* ensure most recent version of pip is installed to virtualenv on creation

0.2.2
=====

* fix error in construction of list of packages to install

0.2.1
=====

* add ``mkvenv init --check``

0.2.0
=====

* rename ``mkvenv wheelhouse`` to ``mkvenv init``


0.1.6
=====

* allow packages to be specified as urls (eg, git repos)
* remove deprecated 'pip --download-cache'

0.1.5
=====

* install packages in requirements file before those provided on command line
* post-tag version numbering complies with PEP 440

0.1.4
=====

* fix error calculating version number

0.1.3
=====

* installation to system requires --system
* remove global --system option
* default WHEELHOUSE is ~/.mkvenv
* change 'wheel' command to 'wheelhouse'

0.1.2
=====

* installs to system python if --venv not specified
* install performs --upgrade
* --version writes to stdout

0.1.1
=====

* initial release!

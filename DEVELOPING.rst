=====================
 developing mkrefpkg
=====================

Versioning
==========

A version number is set within the package at the time of installation
or packaging into a tarball or wheel based on the value of `git
describe --tags --dirty`. Tags should be set using the format
"<major>.<minor>.<release>" (eg "0.1.0"). For example::

  git tag -a -m "version 0.1.0" 0.1.0

Don't forget to push the new tag afterwards along with any new commits::

  git push origin master
  git push --tags


PyPi
====

If you have not done so create a ~/.pypirc file::

  python setup.py register

Proceed to build and upload::

  rm -rf build dist
  python setup.py sdist bdist_wheel
  twine upload dist/*

#!/usr/bin/env python

"""Install a virtualenv, downloading the source if necessary

"""

import os
import sys
import argparse
import imp
import tarfile

from os import path
from urllib2 import urlopen
from distutils.version import LooseVersion


def fetch(url, dest_dir=''):
    if dest_dir:
        try:
            os.makedirs(dest_dir)
        except OSError:
            pass

    fname = path.join(dest_dir, path.basename(url))
    if not path.exists(fname):
        handle = urlopen(url)
        with open(fname, "wb") as f:
            f.write(handle.read())
        handle.close()

    return fname


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('venv', help="Absolute or relative path to a virtualenv")
    parser.add_argument('--src', default='src',
                        help="Directory for downloaded source code")

    args = parser.parse_args(arguments)

    py_version = "{}.{}.{}".format(*sys.version_info[:3])
    venv_url = 'https://pypi.python.org/packages/source/v/virtualenv'
    venv_version = '1.11.6'
    venv_tgz = 'virtualenv-{}.tar.gz'.format(venv_version)

    venv = args.venv

    if not path.exists(path.join(venv, 'bin', 'activate')):
        try:
            import virtualenv
            if not LooseVersion(virtualenv.__version__) < LooseVersion(venv_version):
                raise ImportError
        except ImportError:
            archive = fetch(path.join(venv_url, venv_tgz), dest_dir=args.src)

            with tarfile.open(archive, 'r') as tfile:
                tfile.extractall(args.src)

            virtualenv = imp.load_source(
                'virtualenv',
                path.join(archive.replace('.tar.gz', ''), 'virtualenv.py'))

        virtualenv.create_environment(venv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


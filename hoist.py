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

VENV_URL = 'https://pypi.python.org/packages/source/v/virtualenv'
VENV_VERSION = '1.11.6'


def fetch(url, dest_dir='.'):

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


def create_virtualenv(venv, version=VENV_VERSION, base_url=VENV_URL, srcdir='.'):

    venv_tgz = 'virtualenv-{}.tar.gz'.format(version)

    if path.exists(path.join(venv, 'bin', 'activate')):
        print('virtualenv {} already exists'.format(venv))
    else:
        try:
            import virtualenv
            if not LooseVersion(virtualenv.__version__) < LooseVersion(version):
                raise ImportError
            print('using system version of virtualenv')
        except ImportError:
            print('downloading and extracting virtualenv source to {}'.format(srcdir))
            archive = fetch(path.join(base_url, venv_tgz), dest_dir=srcdir)
            with tarfile.open(archive, 'r') as tfile:
                tfile.extractall(srcdir)

            virtualenv = imp.load_source(
                'virtualenv',
                path.join(archive.replace('.tar.gz', ''), 'virtualenv.py'))

        print('creating virtualenv {}'.format(venv))
        virtualenv.create_environment(venv)


def create(args):
    create_virtualenv(args.venv, srcdir=args.src)


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers()

    parser_create = subparsers.add_parser('create', help='create a new virtualenv')
    parser_create.set_defaults(func=create)
    parser_create.add_argument('venv', help="Absolute or relative path to a virtualenv")
    parser_create.add_argument('--src', default='src',
                               help="Directory for downloaded source code")

    args = parser.parse_args(arguments)
    args.func(args)

    # py_version = "{}.{}.{}".format(*sys.version_info[:3])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


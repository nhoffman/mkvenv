#!/usr/bin/env python

"""Install a virtualenv, downloading the source if necessary

"""

import os
import sys
import argparse
import imp
import tarfile
import textwrap
import subprocess

from os import path
from urllib2 import urlopen
from distutils.version import LooseVersion

VENV_URL = 'https://pypi.python.org/packages/source/v/virtualenv'
VENV_VERSION = '1.11.6'

PY_VERSION = "{}.{}.{}".format(*sys.version_info[:3])
WHEELSTREET_SYSTEM = os.environ.get('WHEELSTREET', '/usr/local/share/python/wheels')
WHEELSTREET_USER = os.environ.get('WHEELSTREET', '~/wheels')

WHEEL_PKG = 'wheel==0.24.0'


def mkdir(pth):
    try:
        os.makedirs(pth)
    except OSError:
        pass

    return path.abspath(pth)


def fetch(url, dest_dir='.'):

    mkdir(dest_dir)
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


class Subparser(object):
    def __init__(self, subparsers, name):
        self.subparser = subparsers.add_parser(
            name,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help=self.__doc__.strip().split('\n')[0],
            description=textwrap.dedent(self.__doc__.rstrip()))
        self.subparser.set_defaults(func=self.action)
        self.add_arguments()


class Virtualenv(Subparser):
    """
    Create a new virtualenv
    """

    def add_arguments(self):
        self.subparser.add_argument(
            'venv', help="Path to a virtualenv")
        self.subparser.add_argument(
            '--src', default='src', help="Directory for downloaded source code")

    def action(self, args):
        create_virtualenv(args.venv, srcdir=args.src)


class Wheel(Subparser):
    """
    Create the WHEELHOUSE, optionally building wheels
    """

    def add_arguments(self):
        self.subparser.add_argument(
            '-w', '--wheelstreet', default=WHEELSTREET_USER,
            help="""Directory for wheels and virtualenv [%(default)s]""")
        self.subparser.add_argument(
            '-r', '--requirements',
            help="""file containing list of packages to install"""
        )

    def action(self, args):
        wheelhouse = path.join(args.wheelstreet, PY_VERSION)
        src = path.join(wheelhouse, 'src')
        cache = path.join(wheelhouse, 'cache')
        venv = path.join(wheelhouse, 'venv')
        create_virtualenv(venv, src)

        pip = path.join(venv, 'bin', 'pip')

        subprocess.check_call(
            [pip, 'install', '--download-cache', cache, WHEEL_PKG])

        if args.requirements:
            with open(args.requirements) as f:
                for pkg in f:
                    subprocess.check_call([
                        pip, 'wheel', pkg,
                        '--download-cache', cache,
                        '--use-wheel',
                        '--find-links', wheelhouse,
                        '--wheel-dir', wheelhouse
                    ])

                    subprocess.check_call([
                        pip, 'install', pkg,
                        '--use-wheel',
                        '--no-index',
                        '--find-links', wheelhouse
                    ])


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers()
    Virtualenv(subparsers, name='virtualenv')
    Wheel(subparsers, name='wheel')

    args = parser.parse_args(arguments)
    print('using {} ({})'.format(sys.executable, PY_VERSION))
    args.func(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


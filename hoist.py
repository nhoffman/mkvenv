#!/usr/bin/env python

"""Streamline the creation of virtualenvs and use of wheels.

 * Create and maintain a cache of wheels.
 * Create a virtualenv and install packages from the wheel cache in a
   single command.
 * Add to the wheel cache as new packages are built.

The sources for the ``virtualenv`` package are downloaded and used to
create the virtualenv if uninstalled or not up to date, so the only
dependency should be a python interpreter (version 2.7.x only for
now).

The location of the wheel cache (the "wheelstreet") is determined as
follows:

 * The default location is '~/wheels' (or
   /usr/local/share/python/wheels if the --system option is used); or
 * the environment variable ``$WHEELSTREET``; or
 * a path specified using the ``-w/--wheelstreet`` option.

Within the "wheelstreet" directory, wheels are saved within a
subdirectory (the "wheelhouse") named according to the version of the
python interpreter (eg '~/wheels/2.7.9/'). In this way, wheels built
againt different versions of the interpreter may coexist.

The target virtualenv is either:

 * An active virtualenv (indicated by the ``$VIRTUAL_ENV``); or
 * as indicated on the command line.

Packages are specified in a requirements file in the same format used
by pip. Lines starting with '-e', '#', or containing a path separator
('/') are skipped. Unlike pip, packages are guaranteed to be installed
in the order specified; this is important for packages for which
installation fails in the absence of already-installed dependencies.

"""

import argparse
import imp
import glob
import os
import subprocess
import shutil
import sys
import tarfile
import tempfile
import textwrap
import logging

from os import path
from urllib2 import urlopen
from distutils.version import LooseVersion

log = logging

VENV_URL = 'https://pypi.python.org/packages/source/v/virtualenv'
VENV_VERSION = '1.11.6'

PY_VERSION = "{}.{}.{}".format(*sys.version_info[:3])
WHEELSTREET_SYSTEM = os.environ.get('WHEELSTREET', '/usr/local/share/python/wheels')
WHEELSTREET_USER = os.environ.get('WHEELSTREET', '~/wheels')

WHEEL_PKG = 'wheel>=0.24.0'


def mkdir(pth):
    try:
        os.makedirs(pth)
    except OSError:
        pass

    return path.abspath(pth)


def fetch(url, dest_dir='.'):

    log.info('downloading {} to {}'.format(url, dest_dir))

    mkdir(dest_dir)
    fname = path.join(dest_dir, path.basename(url))
    if not path.exists(fname):
        handle = urlopen(url)
        with open(fname, "wb") as f:
            f.write(handle.read())
        handle.close()

    return fname


def read_requirements(fname):
    with open(fname) as f:
        for line in f:
            if line.startswith('#') or line.startswith('-e') or '/' in line:
                log.info('skipping {}'.format(line.strip()))
                continue
            yield line.strip()


def pip_install(venv, pkg, wheelhouse=None, quiet=False):
    pip = path.join(venv, 'bin', 'pip')
    cmd = [pip, 'install', pkg]

    if wheelhouse and path.exists(wheelhouse):
        cmd += ['--use-wheel', '--find-links', wheelhouse, '--no-index']

    if quiet:
        cmd += ['--quiet']

    subprocess.check_call(cmd)


def pip_show(venv, pkg):
    pip = path.join(venv, 'bin', 'pip')
    cmd = [pip, 'show', pkg]
    output = subprocess.check_output(cmd)
    return output, pkg in output


def pip_wheel(wheelhouse, pkg, quiet=False):
    cache = path.join(wheelhouse, 'cache')
    venv = path.join(wheelhouse, 'venv')
    pip = path.join(venv, 'bin', 'pip')
    cmd = [
        pip, 'wheel', pkg,
        '--download-cache', cache,
        '--use-wheel',
        '--find-links', wheelhouse,
        '--wheel-dir', wheelhouse
    ]

    if quiet:
        cmd += ['--quiet']

    subprocess.check_call(cmd)


def wheel_paths(args):

    wheelstreet = args.wheelstreet \
        or os.environ.get('WHEELSTREET') \
        or (WHEELSTREET_SYSTEM if args.system else WHEELSTREET_USER)
    wheelstreet = expand(wheelstreet)
    wheelhouse = path.join(wheelstreet, PY_VERSION)

    return wheelstreet, wheelhouse, path.exists(wheelhouse)

def expand(pth):
    if pth:
        return path.abspath(path.expanduser(pth))
    else:
        return pth

def create_virtualenv(venv, version=VENV_VERSION, base_url=VENV_URL, srcdir=None):

    venv = expand(venv)
    venv_tgz = 'virtualenv-{}.tar.gz'.format(version)
    src_is_temp = False

    if path.exists(path.join(venv, 'bin', 'activate')):
        log.info('virtualenv {} already exists'.format(venv))
    else:
        try:
            # raise ImportError
            import virtualenv
            if LooseVersion(virtualenv.__version__) < LooseVersion(version):
                raise ImportError
            log.info('using system version of virtualenv')
        except ImportError:
            log.info('downloading and extracting virtualenv source to {}'.format(srcdir))

            src_is_temp = not srcdir
            srcdir = srcdir or tempfile.mkdtemp()
            archive = fetch(path.join(base_url, venv_tgz), dest_dir=srcdir)
            with tarfile.open(archive, 'r') as tfile:
                tfile.extractall(srcdir)

            virtualenv = imp.load_source(
                'virtualenv',
                path.join(archive.replace('.tar.gz', ''), 'virtualenv.py'))

        log.info('creating virtualenv {}'.format(venv))
        virtualenv.create_environment(venv)

        if src_is_temp:
            shutil.rmtree(srcdir)


class Subparser(object):
    def __init__(self, subparsers, name):
        self.subparser = subparsers.add_parser(
            name,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help=self.__doc__.strip().split('\n')[0],
            description=textwrap.dedent(self.__doc__.rstrip()))
        self.subparser.set_defaults(func=self.action)
        self.add_arguments()


class Show(Subparser):
    """
    Check the status of a package.

    Lists wheels representing `pkg`, or describes whether `pkg` is
    installed if a virtualenv is active or specified with --venv. In
    either case, exits with nonzero status if not found.

    """

    def add_arguments(self):
        self.subparser.add_argument(
            'pkg', help="name of a package")
        self.subparser.add_argument(
            '--venv', help="Path to a virtualenv")

    def action(self, args):
        venv = expand(args.venv or os.environ.get('VIRTUAL_ENV'))
        retval = 1
        if venv:
            output, is_installed = pip_show(venv, args.pkg)
            if is_installed:
                retval = 0
                print(output.strip())
            else:
                print('package {} is not installed in {}'.format(args.pkg, venv))
        else:
            wheelstreet, wheelhouse, wheelhouse_exists = wheel_paths(args)
            found_wheel = glob.glob(path.join(wheelhouse, args.pkg + '*'))
            if found_wheel:
                retval = 0
                for whl in found_wheel:
                    print(whl)
            else:
                print('no wheel for {} in {}'.format(args.pkg, wheelhouse))

        return retval


class Virtualenv(Subparser):
    """
    Create a new virtualenv
    """

    def add_arguments(self):
        self.subparser.add_argument(
            'venv', help="Path to a virtualenv")

    def action(self, args):
        create_virtualenv(args.venv)


class Install(Subparser):
    """
    Install packages to a virtualenv, optionally building and caching wheels

    If the path specified by --venv does not exist, create it.
    """

    def add_arguments(self):
        self.subparser.add_argument(
            '--venv', help="path to a virtualenv (defaults to active virtualenv)",
            default=os.environ.get('VIRTUAL_ENV'))
        self.subparser.add_argument(
            '-r', '--requirements',
            help="""file containing list of packages to install""")
        self.subparser.add_argument(
            '--no-cache', dest='cache', action='store_false', default=True,
            help="""do not build and cache wheels in WHEELHOUSE/{}""".format(
                PY_VERSION))

    def action(self, args):
        quiet=args.verbosity < 1
        venv = expand(args.venv or os.environ.get('VIRTUAL_ENV'))

        if not venv:
            sys.exit('a virtualenv must be active or a path specified using --venv')

        log.info('installing packages to virtualenv {}'.format(args.venv))

        wheelstreet, wheelhouse, wheelhouse_exists = wheel_paths(args)

        if args.cache:
            if not wheelhouse_exists:
                sys.exit(('{} does not exist - you can '
                          'create it using the `wheel` command').format(wheelhouse))
                log.info('caching wheels to {}'.format(wheelhouse))
            wheel_venv = path.join(wheelhouse, 'venv')

        create_virtualenv(venv)

        if args.requirements:
            for pkg in read_requirements(args.requirements):
                if args.cache:
                    pip_wheel(wheelhouse, pkg, quiet=quiet)
                    pip_install(wheel_venv, pkg, wheelhouse, quiet=quiet)
                pip_install(venv, pkg, wheelhouse if wheelhouse_exists else None,
                            quiet=quiet)


class Wheel(Subparser):
    """
    Create the WHEELHOUSE, optionally building wheels
    """

    def add_arguments(self):
        self.subparser.add_argument(
            '-r', '--requirements',
            help="""file containing list of packages to install"""
        )

    def action(self, args):

        # create WHEELSTREET/{PY_VERSION} and virtualenv if necessary
        wheelstreet, wheelhouse, wheelhouse_exists = wheel_paths(args)

        quiet=args.verbosity < 1

        venv = path.join(wheelhouse, 'venv')
        create_virtualenv(venv)
        pip_install(venv, WHEEL_PKG, quiet=quiet)

        # install packages if specified
        if args.requirements:
            for pkg in read_requirements(args.requirements):
                pip_wheel(wheelhouse, pkg, quiet=quiet)
                pip_install(venv, pkg, wheelhouse, quiet=quiet)


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '--system', action='store_true', default=False,
        help="""use {} for the default location of wheels (rather than
        {})""".format(WHEELSTREET_SYSTEM, WHEELSTREET_USER))
    parser.add_argument(
        '-w', '--wheelstreet',
        help="""install wheels in WHEELSTREET/{} instead of the
        default location (may also be specified by defining a shell
        environment variable $WHEELSTREET)""".format(PY_VERSION))
    parser.add_argument(
        '-v', action='count', dest='verbosity', default=1,
        help='Increase verbosity of screen output (eg, -v is verbose, '
        '-vv more so)')
    parser.add_argument(
        '-q', '--quiet', action='store_const', dest='verbosity', const=0,
        help='Suppress screen output from pip commands')


    subparsers = parser.add_subparsers()
    Virtualenv(subparsers, name='virtualenv')
    Wheel(subparsers, name='wheel')
    Install(subparsers, name='install')
    Show(subparsers, name='show')

    args = parser.parse_args(arguments)

    # set up logging
    loglevel = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }.get(args.verbosity, logging.DEBUG)

    logformat = '%(levelname)s %(message)s' if args.verbosity > 1 else '%(message)s'
    logging.basicConfig(file=sys.stderr, format=logformat, level=loglevel)

    log.info('using {} ({})'.format(sys.executable, PY_VERSION))
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

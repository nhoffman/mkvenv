#!/usr/bin/env python

"""Wrapper for virtualenv, pip, and wheel

 * Create and maintain a cache of wheels.
 * Create a virtualenv and install packages from the wheel cache in a
   single command.
 * Add to the wheel cache as new packages are built.
 * Download the ``virtualenv`` source code when not already installed
   or out of date.

The sources for the ``virtualenv`` package are downloaded and used to
create the virtualenv if uninstalled or not up to date, so the only
dependency should be a python interpreter (version 2.7.x only for
now).

The location of the wheel cache (the "wheelstreet") is determined as
follows:

 * ``~/.mkvenv`` (the default location); or
 * the environment variable ``$WHEELSTREET``; or
 * a path specified using the ``-w/--wheelstreet`` option for a specific command.

Within the "wheelstreet" directory, wheels are saved within a
subdirectory (the "wheelhouse") named according to the version of the
python interpreter (eg '~/.mkvenv/2.7.9/'). In this way, wheels built
against different versions of the interpreter may coexist.

The target virtualenv is either:

 * An active virtualenv (indicated by the ``$VIRTUAL_ENV``); or
 * indicated on the command line.

Packages are specified in a requirements file in the same format used
by pip. Lines starting with '-e', '#', or containing a path separator
('/') are skipped. Unlike pip, packages are guaranteed to be installed
in the order specified; this is important for packages for which
installation fails in the absence of already-installed dependencies.

For usage examples see https://github.com/nhoffman/mkvenv
"""

import argparse
import glob
import imp
import itertools
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap

from os import path
from urllib2 import urlopen
from distutils.version import LooseVersion

try:
    with open(path.join(path.dirname(__file__), 'data', 'ver')) as f:
        __version__ = f.read().strip().replace('-', '+', 1).replace('-', '.')
except Exception, e:
    __version__ = ''

log = logging

VENV_URL = 'https://pypi.python.org/packages/source/v/virtualenv'
VENV_VERSION = '1.11.6'

PY_VERSION = "{}.{}.{}".format(*sys.version_info[:3])
WHEELSTREET = '~/.mkvenv'

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
    if not fname:
        raise StopIteration

    with open(fname) as f:
        for line in [x.strip() for x in f]:
            if not line or line.startswith('#') or line.startswith('-e') or '/' in line:
                log.info('skipping {}'.format(line))
                continue
            log.info(line)
            yield line


def pip_install(pkg, pip='pip', venv=None, wheelhouse=None, quiet=False):
    pip = path.join(venv, 'bin', 'pip') if venv else pip
    cmd = [pip, 'install', pkg, '--upgrade']

    if wheelhouse and path.exists(wheelhouse):
        cmd += ['--use-wheel', '--find-links', wheelhouse, '--no-index']

    if quiet:
        cmd += ['--quiet']

    log.info(' '.join(cmd))

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
    wheelstreet = args.wheelstreet or os.environ.get('WHEELSTREET') or WHEELSTREET
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
            log.info(
                'downloading and extracting virtualenv source to {}'.format(srcdir))

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


class List(Subparser):
    """
    List wheels
    """

    def add_arguments(self):
        pass

    def action(self, args):
        wheelstreet, wheelhouse, wheelhouse_exists = wheel_paths(args)
        if wheelhouse_exists:
            log.warning('# Wheels in {}/'.format(wheelhouse))
            for whl in glob.glob(path.join(wheelhouse, '*.whl')):
                print(path.basename(whl))
        else:
            log.warning('The directory {} does not exist - use the `wheelhouse` '
                        'subcommand to create it'.format(wheelhouse))


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
            'packages', nargs='*',
            help="""one or more packages (installed after packages
            listed in the requirements file)""")
        self.subparser.add_argument(
            '--venv', help="path to a virtualenv (defaults to active virtualenv)",
            default=os.environ.get('VIRTUAL_ENV'))
        self.subparser.add_argument(
            '-r', '--requirements',
            help="""file containing list of packages to install""")
        self.subparser.add_argument(
            '--system', action='store_true', default=False,
            help=('install packages to the system version '
                  'of the Python interpreter when --venv is undefined'))
        self.subparser.add_argument(
            '--no-cache', dest='cache', action='store_false', default=True,
            help="""do not build and cache wheels in WHEELHOUSE/{}""".format(
                PY_VERSION))

    def action(self, args):
        quiet = args.verbosity < 1
        venv = expand(args.venv or os.environ.get('VIRTUAL_ENV'))

        if venv:
            create_virtualenv(venv)
            log.info('installing packages to virtualenv {}'.format(args.venv))
        elif args.system:
            log.info('installing packages using {}'.format(sys.executable))
        else:
            log.error('Error: no virtualenv is defined. Use --system to install using '
                      'the current Python interpreter ({})'.format(sys.executable))
            sys.exit(1)

        wheelstreet, wheelhouse, wheelhouse_exists = wheel_paths(args)

        if args.cache:
            if not wheelhouse_exists:
                sys.exit(('{} does not exist - you can create it '
                          'using the `wheelhouse` command').format(wheelhouse))
            log.info('caching wheels to {}'.format(wheelhouse))

        wheelhouse = wheelhouse if (wheelhouse_exists and args.cache) else None
        for pkg in itertools.chain(read_requirements(args.requirements), args.packages):
            if args.cache:
                pip_wheel(wheelhouse, pkg, quiet=quiet)
                pip_install(pkg, venv=path.join(wheelhouse, 'venv'),
                            wheelhouse=wheelhouse, quiet=quiet)
            pip_install(pkg, venv=venv, wheelhouse=wheelhouse, quiet=quiet)


class Wheel(Subparser):
    """
    Create the WHEELHOUSE, optionally building wheels
    """

    def add_arguments(self):
        self.subparser.add_argument(
            'packages', nargs='*',
            help="""one or more packages (installed before packages
            listed in requirements file)""")
        self.subparser.add_argument(
            '-r', '--requirements',
            help="""file containing list of packages to install"""
        )

    def action(self, args):

        # create WHEELSTREET/{PY_VERSION} and virtualenv if necessary
        wheelstreet, wheelhouse, wheelhouse_exists = wheel_paths(args)

        quiet = args.verbosity < 1

        venv = path.join(wheelhouse, 'venv')
        create_virtualenv(venv)
        pip_install(WHEEL_PKG, venv=venv, quiet=quiet)

        # install packages if specified
        for pkg in itertools.chain(read_requirements(args.requirements), args.packages):
            pip_wheel(wheelhouse, pkg, quiet=quiet)
            pip_install(pkg, venv=venv, wheelhouse=wheelhouse, quiet=quiet)


class VersionAction(argparse._VersionAction):
    """Write the version string to stdout and exit"""
    def __call__(self, parser, namespace, values, option_string=None):
        formatter = parser._get_formatter()
        formatter.add_text(parser.version if self.version is None else self.version)
        sys.stdout.write(formatter.format_help())
        sys.exit(0)


def main(arguments=None):

    if arguments is None:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-w', '--wheelstreet',
        help="""install wheels in WHEELSTREET/{} instead of the
        default location (may also be specified by defining a shell
        environment variable $WHEELSTREET)""".format(PY_VERSION))
    parser.add_argument(
        '-v', action='count', dest='verbosity', default=1,
        help='increase verbosity of screen output (eg, -v is verbose, '
        '-vv more so)')
    parser.add_argument(
        '-q', '--quiet', action='store_const', dest='verbosity', const=0,
        help='suppress screen output from pip commands')
    parser.add_argument(
        '-V', '--version', action=VersionAction, version=__version__,
        help='Print the version number and exit')

    subparsers = parser.add_subparsers()
    Virtualenv(subparsers, name='virtualenv')
    Wheel(subparsers, name='wheelhouse')
    Install(subparsers, name='install')
    Show(subparsers, name='show')
    List(subparsers, name='list-wheels')

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

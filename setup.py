import os
import subprocess
from setuptools import setup, find_packages

subprocess.call(
    ('mkdir -p mkvenv/data && '
     'git describe --tags --dirty > mkvenv/data/ver.tmp'
     '&& mv mkvenv/data/ver.tmp mkvenv/data/ver '
     '|| rm -f mkvenv/data/ver.tmp'),
    shell=True, stderr=open(os.devnull, "w"))

from mkvenv.mkvenv import __version__

setup(
    author='Noah Hoffman',
    author_email='noah.hoffman@gmail.com',
    description='Wrapper for virtualenv, pip, and wheel',
    url='https://github.com/nhoffman/mkvenv',
    name='mkvenv',
    packages=find_packages(),
    package_dir={'mkvenv': 'mkvenv'},
    package_data={'mkvenv': ['data/ver']},
    entry_points={'console_scripts': ['mkvenv = mkvenv.mkvenv:main']},
    version=__version__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
    ],
)

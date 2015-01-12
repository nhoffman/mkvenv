from setuptools import setup, find_packages
from mkvenv.mkvenv import __version__

setup(
    author='Noah Hoffman',
    author_email='noah.hoffman@gmail.com',
    description='Wrapper for virtualenv, pip, and wheel',
    name='mkvenv',
    packages=find_packages(),
    package_dir={'mkvenv': 'mkvenv'},
    entry_points={'console_scripts': ['mkvenv = mkvenv.mkvenv:main']},
    version=__version__
)

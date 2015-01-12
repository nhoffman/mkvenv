from setuptools import setup, find_packages
from petard.hoist import __version__

params = {'author': 'Noah Hoffman',
          'author_email': 'noah.hoffman@gmail.com',
          'description': 'Wrapper for virtualenv, pip, and wheel',
          'name': 'petard',
          'packages': find_packages(),
          'package_dir': {'petard': 'petard'},
          'entry_points': {
              'console_scripts': ['hoist = petard.hoist:main']
          },
          'version': __version__,
          }

setup(**params)

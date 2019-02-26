import sys
from setuptools import setup
from distutils.util import get_platform


if sys.version_info < (3, 4):
    sys.stderr.write('This module requires at least Python 3.4\n')
    sys.exit(1)

require_libs = ['PyYAML>=3.13', 'jmespath>=0.9.3']

platform = get_platform()
if platform.startswith('linux') or platform.startswith('freebsd'):
    require_libs.append('pyinotify==0.9.6')

with open('README.md') as f:
    long_description = f.read().strip()


setup(
    name='myconf',
    description='load json or yaml files as python dict, auto refresh when file changing, support item changing callback',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    version='1.1.0',
    author='thuhak',
    author_email='thuhak.zhou@nio.com',
    keywords='configfile',
    packages =['myconf'],
    url='https://github.com/thuhak/myconf',
    install_requires=require_libs
)

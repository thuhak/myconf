import sys
from setuptools import setup
from distutils.util import get_platform


if sys.version_info < (3, 4):
    sys.stderr.write('This module requires at least Python 3.4\n')
    sys.exit(1)

require_libs = ['PyYAML>=3.13']

platform = get_platform()
if platform.startswith('linux') or platform.startswith('freebsd'):
    require_libs.append('pyinotify==0.9.6')


setup(
    name='myconf',
    version='1.0.1',
    author='thuhak',
    author_email='thuhak.zhou@nio.com',
    description='load json or yaml files as python dict, auto refresh when file changing',
    keywords='config file loader',
    packages =['myconf'],
    url='https://github.com/thuhak/myconf',
    install_requires=require_libs
)

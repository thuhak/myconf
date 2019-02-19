import os
from setuptools import setup


def openf(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


setup(
    name='myconf',
    version='1.0.0',
    author='thuhak',
    author_email='thuhak.zhou@nio.com',
    description='load json or yaml files as python dict, auto refresh when file changing',
    keywords='config file loader',
    packages =['myconf'],
    url='https://github.com/thuhak/myconf',
    install_requires=[line.strip() for line in openf("requirements.txt") if line.strip()]
)

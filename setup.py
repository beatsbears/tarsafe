
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

from tarsafe import __version__

with open(path.join(here, 'README.md')) as file:
    long_description = file.read()

setup(
    name='tarsafe',
    version=__version__,
    description='A safe subclass of the TarFile class for interacting with tar files. Can be used as a direct drop-in replacement for safe usage of extractall()',
    long_description=long_description,
    author='Andrew Scott',
    url='https://github.com/beatsbears/tarsafe',
    packages=find_packages(exclude=['tests*']),
    license='MIT License',
    install_requires=[],
    python_requires='>=3.6'
)
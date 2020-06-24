# Tarsafe
![Unit Tests](https://github.com/beatsbears/tarsafe/workflows/Unit%20Tests/badge.svg)

Tarsafe is a drop-in replacement for the tarfile module from the standard library to safely handle the vulnerable `extractall()` method. Inspired by a [6 year old security bug](https://bugs.python.org/issue21109).

## Installation
```
$ pip install tarsafe
```

## Usage
```
import sys

from tarsafe import TarSafe

tar = TarSafe.open(sys.argv[1], "r")
tar.extractall()
tar.close()
```
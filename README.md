# Tarsafe
![Unit Tests](https://github.com/beatsbears/tarsafe/workflows/Unit%20Tests/badge.svg)

Tarsafe is a drop-in replacement for the tarfile module from the standard library to safely handle the vulnerable `extractall()` method. Inspired by a [6 year old security bug](https://bugs.python.org/issue21109).

## Installation
```
$ pip install tarsafe
```

## Usage
```
from tarsafe import TarSafe

tar = TarSafe.open("example.tar", "r")
tar.extractall()
tar.close()

# OR

with TarSafe.open("example.tar", "r") as tar:
    tar.extractall()
```
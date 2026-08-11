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

## Note on Python 3.12+
As of Python 3.12, the standard library's `tarfile` has built-in extraction filters ([PEP 706](https://peps.python.org/pep-0706/)) that cover this same class of vulnerability. If you're only targeting 3.12+, `tarfile.TarFile.extractall(..., filter="data")` (or `filter="tar"`) may be a lighter-weight alternative to this library. Tarsafe still supports Python 3.6+, so it remains useful when you need safe extraction on older versions.
import os
import sys
import pytest

from tarsafe import TarSafe, TarSafeException

def test_bad_files():
    files = os.listdir("./test/data/bad")
    for file_ in files:
        with pytest.raises(TarSafeException) as ex:
            with TarSafe.open(f"./test/data/bad/{file_}", "r") as tar:
                tar.extractall()

def test_good_files():
    files = os.listdir("./test/data/good")
    for file_ in files:
        with TarSafe.open(f"./test/data/good/{file_}", "r") as tar:
            tar.extractall()
        assert os.path.exists("./evil.sh")
        os.remove("./evil.sh")

def test_good_file():
    files = os.listdir("./test/data/good")
    for file_ in files:
        with TarSafe.open(f"./test/data/good/{file_}", "r") as tar:
            tar.extract("evil.sh")
        assert os.path.exists("./evil.sh")
        os.remove("./evil.sh")

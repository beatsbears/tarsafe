import os
import sys
import pytest

from src.tarsafe import TarSafe, TarSafeException

def test_all_files():
    files = os.listdir("./test/data")
    for file_ in files:
        with pytest.raises(TarSafeException) as ex:
            with TarSafe.open(f"./test/data/{file_}", "r") as tar:
                tar.extractall()

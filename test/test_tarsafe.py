import os
import sys
import pytest

from tarsafe import TarSafe, TarSafeException

def test_all_files(self):
    files = os.listdir("./data")
    for file_ in files:
        with pytest.raises(TarSafeException) as ex:
            with TarSafe.open(file_, "r") as tar:
                tar.extractall()
            assert ex == "No dependencies files found"

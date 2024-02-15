import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    temp_dir = Path('temp_test_dir')
    temp_dir.mkdir(exist_ok=True)
    yield temp_dir

    # removing the temp_dir
    shutil.rmtree(temp_dir)

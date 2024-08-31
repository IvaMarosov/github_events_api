from pathlib import Path

import pytest


@pytest.fixture
def test_data_file_path():
    data_dir = Path(__file__).parent.parent / "data"

    def _data_file_path(file_name: str) -> Path:
        return (data_dir / file_name).resolve()

    return _data_file_path

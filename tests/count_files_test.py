import pytest

from trope_paths import model_output

subdirs = list(model_output.iterdir())


@pytest.mark.parametrize("subdir", subdirs)
def test_count_files(subdir):
    assert 1500 == len(list(subdir.iterdir()))

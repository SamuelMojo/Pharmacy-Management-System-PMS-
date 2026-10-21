import sys


def test_python_version_is_at_least_3_13():
    assert sys.version_info >= (3, 13)
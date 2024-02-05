"""
Re-useable fixtures etc. for tests

See https://docs.pytest.org/en/7.1.x/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""
from __future__ import annotations

import _pytest.config
import _pytest.config.argparsing
import _pytest.python
import pytest


def pytest_addoption(parser: _pytest.config.argparsing.Parser):
    parser.addoption("--skipslow", action="store_true", default=False, help="skip slow tests")


def pytest_collection_modifyitems(config: _pytest.config.Config, items: list[_pytest.python.Function]):
    if config.getoption("--skipslow"):
        skip_slow = pytest.mark.skip(reason="--skipslow applied")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

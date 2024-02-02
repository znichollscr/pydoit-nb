"""
Test operations

This module is just there to help with doc building etc. on
project creation. You will probably delete it early in the project.
"""
from pydoit_nb.operations import add_two


def test_add_two():
    assert add_two(3, 4) == 7

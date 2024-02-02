"""
Test doit_tools module
"""
from pydoit_nb.doit_tools import swallow_output


def test_swallow_output():
    def raw(inp):
        return inp * 2.0

    wrapped = swallow_output(raw)

    assert raw(3.4) == 6.8, "raw doesn't return anything"

    res = wrapped(3.4)

    assert res is None

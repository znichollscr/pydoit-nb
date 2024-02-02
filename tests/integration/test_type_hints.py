"""
Test that type annotations are correctly flowing through

For more information, see
https://typing.readthedocs.io/en/latest/source/quality.html?highlight=test

Fair warning: this can be extremely fiddly, particularly given that the test
can effectively fail before running because there is some logic in the
parameterisation.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import mypy.api
import pytest

if TYPE_CHECKING:
    import _pytest


TEST_DATA_DIR = Path(__file__).parent / ".." / "test-data" / "type-hinting"


def generate_cases(filename: Path) -> _pytest.mark.structures.MarkDecorator:
    res = mypy.api.run([str(filename)])

    mypy_stdout = res[0]
    mypy_res: dict[int, str] = {}
    for line in mypy_stdout.split("\n"):
        if not line:
            continue

        if "Success" in line:
            mypy_res[-1] = line.strip()
            continue

        try:
            line_number = int(re.search(rf"{filename.name}:(?P<line_number>\d*)", line).group("line_number"))
        except ValueError:
            print(mypy_stdout)
            raise

        try:
            res = re.search(r'Revealed type is (?P<res>".*")', line).group("res").strip()
        except:
            print(mypy_stdout)
            raise

        mypy_res[line_number] = res

    with open(filename) as fh:
        raw_contents = fh.read()

    in_block = False
    file_cases = []
    idc = None
    for ln, line in enumerate(raw_contents.split("\n")):
        line_number = ln + 1
        if in_block:
            if line.startswith("# exp"):
                exp = re.search(r"exp: (?P<exp>.*)", line).group("exp").strip()

            if line.startswith("reveal_type"):
                assert idc is not None
                file_cases.append([mypy_res[line_number], exp, idc])

                in_block = False
                exp = None
                idc = None

        if line.startswith("# id"):
            in_block = True
            idc = re.search(r"id: (?P<id>\S*)", line).group("id").strip()

    cases = [
        pytest.param(res, exp, mypy_stdout, id=f"{filename.stem}_{idp}")
        for res, exp, idp in [(mypy_res[-1], "Success", "overall-success"), *file_cases]
    ]

    return pytest.mark.parametrize("res, exp, mypy_stdout", cases)


def run_case(res, exp, mypy_stdout):
    if "Success" in exp:
        assert exp in res, mypy_stdout

        return

    assert res == exp, mypy_stdout


@generate_cases(TEST_DATA_DIR / "serialization" / "simple.case")
def test_simple_verify_units(res, exp, mypy_stdout):
    run_case(res, exp, mypy_stdout)

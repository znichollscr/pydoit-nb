"""
Test completion behaviour
"""
import datetime as dt

from pydoit_nb.complete import write_complete_file


def test_write_complete_file(tmp_path):
    contents = "Some interesting information"
    out_file = tmp_path / "complete.txt"
    write_complete_file(out_file, contents=contents)

    with open(out_file) as fh:
        res = fh.read()

    assert res == contents


def test_write_complete_file_default(tmp_path):
    out_file = tmp_path / "complete.txt"
    write_complete_file(out_file)

    with open(out_file) as fh:
        res = fh.read()

    # Make sure this can be converted to a date
    # (don't test the actual date as this could be flaky depending on execution time)
    dt.datetime.strptime(res, "%Y%m%d%H%M%S")

"""
Test checklist file handling
"""
from pathlib import Path

import pytest

from pydoit_nb.checklist import (
    create_md5_dict,
    generate_directory_checklist,
    get_file_md5,
)


def test_create_md5_dict(tmp_path):
    files_to_create = ["a.csv", "b.txt", "c"]
    exp = {}
    for f in files_to_create:
        with open(tmp_path / f, "w") as fh:
            fh.write(f"{f} contents")

        exp[tmp_path / f] = get_file_md5(tmp_path / f)

    res = create_md5_dict(exp.keys())

    assert res == exp


@pytest.mark.parametrize(
    "files_to_create, files_not_excluded, exclusions",
    (
        pytest.param(
            ["a.csv", "b.txt", "c"],
            ["a.csv", "c"],
            [lambda x: x.name.endswith(".txt")],
            id="single_exclusion",
        ),
        pytest.param(
            ["a.csv", "b.txt", "c"],
            ["c"],
            [lambda x: x.name.endswith(".txt"), lambda f: f.name.endswith(".csv")],
            id="two_exclusions",
        ),
    ),
)
def test_create_md5_dict_exclusions(tmp_path, files_to_create, files_not_excluded, exclusions):
    exp = {}
    all_files = []
    for f in files_to_create:
        with open(tmp_path / f, "w") as fh:
            fh.write(f"{f} contents")

        if f in files_not_excluded:
            exp[tmp_path / f] = get_file_md5(tmp_path / f)

        all_files.append(tmp_path / f)

    res = create_md5_dict(all_files, exclusions=exclusions)

    assert res == exp


@pytest.mark.parametrize(
    [
        "checklist_file",
        "exp_checklist_file",
        "files_to_create",
        "exclusions",
        "exp_files",
    ],
    (
        pytest.param(
            None,
            "checklist.chk",  # the default
            ["a.csv", "b.txt", "c"],
            None,
            ["a.csv", "b.txt", "c"],
            id="default_path_no_exclusions",
        ),
        pytest.param(
            Path("subfolder") / "chck.chk",
            Path("subfolder") / "chck.chk",
            ["a.csv", "b.txt", "c"],
            None,
            ["a.csv", "b.txt", "c"],
            id="checklist_file_provided",
        ),
        pytest.param(
            None,
            "checklist.chk",
            ["a.csv", "b.txt", "c"],
            [lambda x: x.name.endswith(".csv"), lambda x: x.name == "c"],
            ["b.txt"],
            id="exclusions",
        ),
    ),
)
def test_generate_directory_checklist(  # noqa: PLR0913
    tmp_path, checklist_file, exp_checklist_file, files_to_create, exclusions, exp_files
):
    call_kwargs = {}

    if checklist_file is None:
        # Checklist file made in directory we're working on
        exp_checklist_file = tmp_path / exp_checklist_file
    else:
        # Put the checklist file in a temporary directory
        exp_checklist_file = tmp_path / exp_checklist_file
        checklist_file = tmp_path / checklist_file
        checklist_file.parent.mkdir(parents=True)
        call_kwargs["checklist_file"] = checklist_file

    if exclusions is not None:
        call_kwargs["exclusions"] = exclusions

    exp_contents = []
    for f in files_to_create:
        with open(tmp_path / f, "w") as fh:
            fh.write(f"{f} contents")

        if f in exp_files:
            f_md5 = get_file_md5(tmp_path / f)
            exp_contents.append(f"{f_md5}  {f}\n")

    exp_contents = "".join(exp_contents)

    res = generate_directory_checklist(tmp_path, **call_kwargs)

    assert res == exp_checklist_file
    with open(res) as fh:
        res_contents = fh.read()

    assert res_contents == exp_contents


def test_not_a_dir_error():
    with pytest.raises(NotADirectoryError):
        generate_directory_checklist(Path("/some") / "junk")

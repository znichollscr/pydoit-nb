"""
Test tasks_copy_source module
"""
import copy
import inspect
import json
import re
from pathlib import Path

import pytest

from pydoit_nb.tasks_copy_source import (
    copy_file_default,
    copy_readme_default,
    copy_tree_default,
    copy_zenodo_default,
    gen_copy_source_into_output_tasks,
    get_pydoit_nb_run_command_default,
)


@pytest.mark.parametrize(
    [
        "readme",
        "readme_exp",
        "zenodo",
        "zenodo_exp",
        "other_files_to_copy",
        "other_files_to_copy_exp",
        "src_dir",
        "src_dir_exp",
        "copy_readme",
        "copy_readme_exp",
        "copy_zenodo",
        "copy_zenodo_exp",
        "copy_file",
        "copy_file_exp",
        "copy_tree",
        "copy_tree_exp",
    ],
    (
        pytest.param(
            "READMOI.md",
            "READMOI.md",
            "hihi.json",
            "hihi.json",
            ("one.txt", "two.csv", Path("subfolder") / "file.txt"),
            ("one.txt", "two.csv", Path("subfolder") / "file.txt"),
            "src-somewhere",
            "src-somewhere",
            "copy-readme-test",
            "copy-readme-test",
            "copy-zenodo-test",
            "copy-zenodo-test",
            "copy-file-test",
            "copy-file-test",
            "copy-tree-test",
            "copy-tree-test",
            id="mocked-out",
        ),
        pytest.param(
            None,
            "README.md",
            None,
            "zenodo.json",
            None,
            ("dodo.py", "poetry.lock", "pyproject.toml"),
            None,
            "src",
            None,
            copy_readme_default,
            None,
            copy_zenodo_default,
            None,
            copy_file_default,
            None,
            copy_tree_default,
            id="defaults",
        ),
    ),
)
def test_gen_copy_source_into_output_tasks(  # noqa: PLR0913
    readme,
    readme_exp,
    zenodo,
    zenodo_exp,
    other_files_to_copy,
    other_files_to_copy_exp,
    src_dir,
    src_dir_exp,
    copy_readme,
    copy_readme_exp,
    copy_zenodo,
    copy_zenodo_exp,
    copy_file,
    copy_file_exp,
    copy_tree,
    copy_tree_exp,
):
    targets_1 = (Path("/to") / "somewhere", Path("/to/other.txt"))
    targets_2 = [Path("/hi/there.csv"), Path("/other/place.nc")]
    all_targets_exp = [*targets_1, *targets_2]
    all_preceeding_tasks = (
        {"tasK": "with no targets"},
        {"task": "name", "targets": targets_1},
        {"task": "other-name", "targets": targets_2, "dependencies": ("a", "b")},
    )

    repo_root_dir = Path("/to") / "repo" / "root"
    root_dir_output_run = Path("/to") / "repo" / "output" / "run" / "id"
    run_id = "test_gen_copy_source_into_output_tasks"
    raw_notebooks_root_dir = repo_root_dir / "notebooks"
    raw_notebooks_output_dir_exp = root_dir_output_run / raw_notebooks_root_dir.relative_to(repo_root_dir)
    config_file_raw = root_dir_output_run / "config-dev-not-absolute.yaml"
    config_file_raw_output_exp = root_dir_output_run / "config-dev-not-absolute-raw.yaml"

    call_kwargs = {}
    if readme is not None:
        call_kwargs["readme"] = readme

    if zenodo is not None:
        call_kwargs["zenodo"] = zenodo

    if other_files_to_copy is not None:
        call_kwargs["other_files_to_copy"] = other_files_to_copy

    if src_dir is not None:
        call_kwargs["src_dir"] = src_dir

    if copy_readme is not None:
        call_kwargs["copy_readme"] = copy_readme

    if copy_zenodo is not None:
        call_kwargs["copy_zenodo"] = copy_zenodo

    if copy_file is not None:
        call_kwargs["copy_file"] = copy_file

    if copy_tree is not None:
        call_kwargs["copy_tree"] = copy_tree

    assert inspect.isgeneratorfunction(gen_copy_source_into_output_tasks)
    # turn into list to force generator to empty
    res = list(
        gen_copy_source_into_output_tasks(
            all_preceeding_tasks=all_preceeding_tasks,
            repo_root_dir=repo_root_dir,
            root_dir_output_run=root_dir_output_run,
            run_id=run_id,
            root_dir_raw_notebooks=raw_notebooks_root_dir,
            config_file_raw=config_file_raw,
            **call_kwargs,
        )
    )

    exp = (
        (
            "copy README",
            [
                (
                    copy_readme_exp,
                    [
                        repo_root_dir / readme_exp,
                        root_dir_output_run / readme_exp,
                        run_id,
                        Path(config_file_raw_output_exp.name),
                    ],
                    {},
                )
            ],
            (root_dir_output_run / readme_exp,),
        ),
        (
            "copy Zenodo",
            [
                (
                    copy_zenodo_exp,
                    [
                        repo_root_dir / zenodo_exp,
                        root_dir_output_run / zenodo_exp,
                        run_id,
                    ],
                    {},
                )
            ],
            (root_dir_output_run / zenodo_exp,),
        ),
        *[
            (
                f"copy {filename}",
                [
                    (
                        copy_file_exp,
                        [
                            repo_root_dir / filename,
                            root_dir_output_run / filename,
                        ],
                        {},
                    )
                ],
                (root_dir_output_run / filename,),
            )
            for filename in other_files_to_copy_exp
        ],
        (
            "copy raw config",
            [
                (
                    copy_file_exp,
                    [
                        config_file_raw,
                        config_file_raw_output_exp,
                    ],
                    {},
                )
            ],
            (config_file_raw_output_exp,),
        ),
        (
            "copy raw notebooks",
            [
                (
                    copy_tree_exp,
                    [
                        raw_notebooks_root_dir,
                        raw_notebooks_output_dir_exp,
                    ],
                    {},
                )
            ],
            (raw_notebooks_output_dir_exp,),
        ),
        (
            "copy source",
            [
                (
                    copy_tree_exp,
                    [
                        repo_root_dir / src_dir_exp,
                        root_dir_output_run / src_dir_exp,
                    ],
                    {},
                )
            ],
            (root_dir_output_run / src_dir_exp,),
        ),
    )
    for i, (name, actions, targets) in enumerate(exp):
        files_short = tuple(f".../{file.name}" for file in targets)
        assert res[i] == {
            "basename": "copy_source_into_output",
            "doc": (
                "Copy required source files into the output directory, making it "
                "easy to create a neat bundle for uploading to Zenodo. "
                f"Copying in {files_short}"
            ),
            "name": name,
            "actions": actions,
            "targets": targets,
            "file_dep": all_targets_exp,
        }

    assert i == len(res) - 1, "Missing something"


def test_abs_path_in_other_files_to_copy_raises():
    absolute_path = Path("/absolute/somewhere.txt")
    error_msg = re.escape(
        f"{absolute_path} is absolute. "
        "`other_files_to_copy` must not contain absolute paths "
        "(all paths are assumed to be relative to `repo_root_dir`)."
    )
    with pytest.raises(ValueError, match=error_msg):
        # list to force generator to flush
        list(
            gen_copy_source_into_output_tasks(
                all_preceeding_tasks=[{"task": "name", "targets": ("file.txt")}],
                repo_root_dir=Path("/somewhere"),
                root_dir_output_run=Path("/elsewhere"),
                run_id="test_abs_path_in_other_files_to_copy_raises",
                root_dir_raw_notebooks=Path("/somewhere") / "notebooks",
                config_file_raw=Path("/somewhere") / "config-dehydrated.yaml",
                other_files_to_copy=("dodo.py", absolute_path),
            )
        )


@pytest.mark.parametrize(
    [
        "raw_run_instruction",
        "raw_run_instruction_exp",
        "get_pydoit_nb_run_command",
        "get_pydoit_nb_run_command_exp",
    ],
    (
        pytest.param(
            None,
            "poetry run doit run --verbosity=2",
            None,
            get_pydoit_nb_run_command_default,
            id="default",
        ),
        pytest.param(
            "run like this",
            "run like this",
            lambda x, y: f"injected {x} {y}",
            lambda x, y: f"injected {x} {y}",
            id="injection",
        ),
    ),
)
def test_copy_readme_default(
    tmp_path,
    raw_run_instruction,
    raw_run_instruction_exp,
    get_pydoit_nb_run_command,
    get_pydoit_nb_run_command_exp,
):
    in_path = tmp_path / "in" / "README.md"
    in_path.parent.mkdir(exist_ok=True, parents=True)
    readme_in_contents = f"""# Test test_copy_readme

Some further contents

Can go here

Like the run instructions.

To run, run

```bash
{raw_run_instruction_exp}
```"""
    with open(in_path, "w") as fh:
        fh.write(readme_in_contents)

    out_path = tmp_path / "out" / "readme.txt"
    out_path.parent.mkdir(exist_ok=True, parents=True)
    run_id = "test_copy_readme"
    # config file is relative to the repository root directory as it gets substituded
    # into the README
    config_file_raw = Path("config") / "config_file_raw.yaml"

    call_kwargs = {}
    if raw_run_instruction is not None:
        call_kwargs["raw_run_instruction"] = raw_run_instruction

    if get_pydoit_nb_run_command is not None:
        call_kwargs["get_pydoit_nb_run_command"] = get_pydoit_nb_run_command

    res = copy_readme_default(
        in_path=in_path,
        out_path=out_path,
        run_id=run_id,
        config_file_raw=config_file_raw,
        **call_kwargs,
    )

    assert res is None

    with open(out_path) as fh:
        res_written = fh.read()

    assert readme_in_contents in res_written
    assert "## Pydoit info" in res_written
    assert get_pydoit_nb_run_command_exp(config_file_raw, raw_run_instruction_exp) in res_written
    if get_pydoit_nb_run_command is None:
        # A more human-readable check
        assert f"DOIT_CONFIGURATION_FILE={config_file_raw} {raw_run_instruction_exp}" in res_written


def test_copy_readme_default_raises_no_raw_run_instruction(tmp_path):
    in_path = tmp_path / "in" / "README.md"
    in_path.parent.mkdir(exist_ok=True, parents=True)
    readme_in_contents = """# Test test_copy_readme

Some further contents (crucially, missing run instructions)"""

    with open(in_path, "w") as fh:
        fh.write(readme_in_contents)

    out_path = tmp_path / "out" / "readme.txt"

    raw_run_instruction = "python run-all.py"

    error_msg = re.escape(
        "Could not find expected run instructions in README. "
        "The injected run instructions probably won't be correct. "
        f"Expected run instruction: {raw_run_instruction}"
    )
    with pytest.raises(AssertionError, match=error_msg):
        copy_readme_default(
            in_path=in_path,
            out_path=out_path,
            run_id="test_copy_readme_default_raises_no_raw_run_instruction",
            config_file_raw=Path("mock"),
            raw_run_instruction=raw_run_instruction,
        )


def test_copy_readme_default_raises_config_file_raw_is_absolute(tmp_path):
    in_path = tmp_path / "in" / "README.md"
    in_path.parent.mkdir(exist_ok=True, parents=True)
    with open(in_path, "w") as fh:
        fh.write("Contents")

    out_path = tmp_path / "out" / "readme.txt"

    config_file_raw = Path("/absolute") / "location"
    error_msg = re.escape(f"``config_file_raw`` must be a relative path, received: {config_file_raw}")
    with pytest.raises(ValueError, match=error_msg):
        copy_readme_default(
            in_path=in_path,
            out_path=out_path,
            run_id="test_copy_readme_default_raises_config_file_raw_is_absolute",
            config_file_raw=config_file_raw,
        )


def test_copy_zenodo_default(tmp_path):
    start = {"metadata": {"title": "Title"}}
    in_path = tmp_path / "in" / "zenodo.json"
    in_path.parent.mkdir(exist_ok=True, parents=True)
    with open(in_path, "w") as fh:
        fh.write(json.dumps(start))

    out_path = tmp_path / "out" / "zenodo-out.json"
    out_path.parent.mkdir(exist_ok=True, parents=True)
    version = "v1.3.2"

    res = copy_zenodo_default(
        in_path=in_path,
        out_path=out_path,
        version=version,
    )

    assert res is None

    with open(out_path) as fh:
        res_written = fh.read()

    res_parsed = json.loads(res_written)
    assert res_parsed["metadata"]["version"] == version

    res_parsed_no_version = copy.deepcopy(res_parsed)
    res_parsed_no_version["metadata"].pop("version")
    # Get rid of starting version in case it was there
    start_no_version = copy.deepcopy(start)
    start_no_version["metadata"].pop("version", None)

    # Now check that the rest of the metadata is unchanged
    assert res_parsed_no_version == start_no_version


# - test copy zenodo
#   - check that version placed in right spot

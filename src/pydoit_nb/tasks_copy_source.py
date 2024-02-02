"""
Generation of tasks for copying source into the outputs
"""
from __future__ import annotations

import json
import shutil
from collections.abc import Callable, Iterable
from functools import partial
from pathlib import Path
from typing import Any, Protocol

from attrs import frozen

from .doit_tools import swallow_output
from .typing import DoitTaskSpec


@frozen
class ActionDef:
    """Definition of an action"""

    name: str
    """Name of the action"""

    action: tuple[Callable[..., Any], list[Any], dict[str, Any]]
    """Action to execute with doit"""

    targets: tuple[Path, ...]
    """Files that this action creates"""


class CopyReadmeCallable(Protocol):
    """Callable which can be used for copying READMEs"""

    def __call__(self, in_path: Path, out_path: Path, run_id: str, config_file_raw: Path) -> None:
        """
        Copy README into the output bundle

        Parameters
        ----------
        in_path
            Path from which to copy the README

        out_path
            Path to copy the README to

        run_id
            ID of the run.

        config_file_raw
            Path to the raw configuration file
        """
        ...  # pragma: no cover


class CopyZenodoCallable(Protocol):
    """Callable which can be used for copying Zenodo JSON files"""

    def __call__(self, in_path: Path, out_path: Path, version: str) -> None:
        """
        Copy Zenodo JSON file into the output bundle

        Parameters
        ----------
        in_path
            Path from which to copy the README

        out_path
            Path to copy the README to

        version
            Version to write in the Zenodo file
        """
        ...  # pragma: no cover


class CopyFileCallable(Protocol):
    """Callable which can be used for copying files"""

    def __call__(self, in_path: Path, out_path: Path) -> None:
        """
        Copy a file from one location to another

        Parameters
        ----------
        in_path
            File to copy

        out_path
            Location to copy to
        """
        ...  # pragma: no cover


class CopyTreeCallable(Protocol):
    """Callable which can be used for copying file trees"""

    def __call__(self, in_path: Path, out_path: Path) -> None:
        """
        Copy a file from one location to another

        Parameters
        ----------
        in_path
            Tree to copy from

        out_path
            Location to copy to
        """
        ...  # pragma: no cover


def gen_copy_source_into_output_tasks(  # noqa: PLR0913
    all_preceeding_tasks: Iterable[DoitTaskSpec],
    repo_root_dir: Path,
    root_dir_output_run: Path,
    run_id: str,
    root_dir_raw_notebooks: Path,
    config_file_raw: Path,
    readme: str = "README.md",
    zenodo: str = "zenodo.json",
    other_files_to_copy: tuple[str | Path, ...] = (
        "dodo.py",
        "poetry.lock",
        "pyproject.toml",
    ),
    src_dir: str = "src",
    copy_readme: CopyReadmeCallable | None = None,
    copy_zenodo: CopyZenodoCallable | None = None,
    copy_file: CopyFileCallable | None = None,
    copy_tree: CopyTreeCallable | None = None,
) -> Iterable[DoitTaskSpec]:
    """
    Generate tasks to copy the source into the output directory

    Parameters
    ----------
    all_preceeding_tasks
        All tasks preceeding this one. The targets of these tasks are set
        as dependencies of this task to ensure that this task runs after them.

    repo_root_dir
        Root directory of the repository. This is used to know where to copy
        files from.

    root_dir_output_run
        Root directory of the run's output. This is used to know where to copy
        files to.

    run_id
        ID of the run.

    root_dir_raw_notebooks
        Root directory to the raw notebooks (these are copied into the output
        bundle to ensure that the bundle can be run standalone)

    config_file_raw
        Path to the raw configuration file

    config_file_raw_output_name
        Name to use when saving the raw configuration file to the output bundle
        (must be different to the hydrated configuration file to avoid a clash)

    readme
        Name of the README file to copy into the output

    zenodo
        Name of the zenodo JSON file to copy into the output

    other_files_to_copy
        Other files to copy into the output (paths are assumed to be relative
        to the project's root)

    src_dir
        Path to the Python source (this is also copied into the output bundle)

    copy_readme
        Callable that copies the README file into the output bundle. If not supplied,
        we use :func:`copy_readme_default`.

    copy_zenodo
        Callable that copies the Zenodo JSON file into the output bundle. If not supplied,
        we use :func:`copy_zenodo_default`.

    copy_file
        Callable that copies a file from one location to another. If not supplied, we use
        :func:`copy_file_default`.

    copy_tree
        Callable that copies a file tree from one location to another. If not supplied, we use
        :func:`copy_tree_default`.

    Yields
    ------
        Tasks for copying the source files into the output directory
    """
    if copy_readme is None:
        copy_readme = copy_readme_default

    if copy_zenodo is None:
        copy_zenodo = copy_zenodo_default

    if copy_file is None:
        copy_file = copy_file_default

    if copy_tree is None:
        copy_tree = copy_tree_default

    all_targets = []
    for task in all_preceeding_tasks:
        if "targets" in task:
            all_targets.extend(task["targets"])

    base_task = {
        "basename": "copy_source_into_output",
        "doc": (
            "Copy required source files into the output directory, making it "
            "easy to create a neat bundle for uploading to Zenodo"
        ),
    }

    output_dir_raw_notebooks = root_dir_output_run / root_dir_raw_notebooks.relative_to(repo_root_dir)

    config_file_raw_output = root_dir_output_run / f"{config_file_raw.stem}-raw{config_file_raw.suffix}"

    action_defs = [
        ActionDef(
            name="copy README",
            action=(
                copy_readme,
                [
                    repo_root_dir / readme,
                    root_dir_output_run / readme,
                    run_id,
                    config_file_raw_output.relative_to(root_dir_output_run),
                ],
                {},
            ),
            targets=(root_dir_output_run / readme,),
        ),
        ActionDef(
            name="copy Zenodo",
            action=(
                copy_zenodo,
                [repo_root_dir / zenodo, root_dir_output_run / zenodo, run_id],
                {},
            ),
            targets=(root_dir_output_run / zenodo,),
        ),
        *get_copy_file_action_definitions(
            repo_root_dir=repo_root_dir,
            root_dir_output_run=root_dir_output_run,
            other_files_to_copy=other_files_to_copy,
            copy_file=copy_file,
        ),
        ActionDef(
            name="copy raw config",
            action=(
                copy_file,
                [config_file_raw, config_file_raw_output],
                {},
            ),
            targets=(config_file_raw_output,),
        ),
        ActionDef(
            name="copy raw notebooks",
            action=(
                copy_tree,
                [root_dir_raw_notebooks, output_dir_raw_notebooks],
                {},
            ),
            targets=(output_dir_raw_notebooks,),
        ),
        ActionDef(
            name="copy source",
            action=(
                copy_tree,
                [repo_root_dir / src_dir, root_dir_output_run / src_dir],
                {},
            ),
            targets=(root_dir_output_run / src_dir,),
        ),
    ]

    for action_def in action_defs:
        created_files_short = tuple(f".../{t.name}" for t in action_def.targets)
        yield {
            "basename": base_task["basename"],
            "doc": f"{base_task['doc']}. Copying in {created_files_short}",
            "name": action_def.name,
            "actions": [action_def.action],
            "targets": action_def.targets,
            "file_dep": all_targets,
        }


def get_copy_file_action_definitions(
    repo_root_dir: Path,
    root_dir_output_run: Path,
    other_files_to_copy: tuple[str | Path, ...],
    copy_file: CopyFileCallable,
) -> Iterable[ActionDef]:
    """
    Get action definitions for copying other files

    Parameters
    ----------
    repo_root_dir
        Root directory of the repository. This is used to know where to copy
        files from.

    root_dir_output_run
        Root directory of the run's output. This is used to know where to copy
        files to.

    other_files_to_copy
        Other files to copy into the output (paths are assumed to be relative
        to the project's root)

    copy_file
        Callable that copies a file from one location to another.

    Returns
    -------
        Action definitions for copying the files

    Raises
    ------
    ValueError
        Any of the values in ``other_files_to_copy`` is an absolute path. Paths
        in ``other_files_to_copy`` are assumed to be relative to ``repo_root_dir``
        hence must be relative.
    """
    copy_file_action_definitions = []
    for file in other_files_to_copy:
        if isinstance(file, Path):
            if file.is_absolute():
                msg = (
                    f"{file} is absolute. "
                    "`other_files_to_copy` must not contain absolute paths "
                    "(all paths are assumed to be relative to `repo_root_dir`)."
                )
                raise ValueError(msg)

        copy_file_action_definitions.append(
            ActionDef(
                name=f"copy {file}",
                action=(
                    copy_file,
                    [repo_root_dir / file, root_dir_output_run / file],
                    {},
                ),
                targets=(root_dir_output_run / file,),
            )
        )

    return copy_file_action_definitions


class GetPydoitNBRunCommandCallable(Protocol):
    """Callable that supports inference of the run command to use with the pydoit-nb output bundle"""

    def __call__(self, config_file_raw: Path, raw_run_instruction: str) -> str:
        """
        Get run command

        This is the default implementation, based on how we have typically set up
        our pydoit-nb based repositories.

        Parameters
        ----------
        config_file_raw
            Path to raw configuration file as it should be used in the run command

        raw_run_instruction
            The command to run the analysis in the README (before the pydoit
            specific instructions are added).

        Returns
        -------
            Run command for use in the pydoit-nb created bundle
        """
        ...  # pragma: no cover


def copy_readme_default(  # noqa: PLR0913
    in_path: Path,
    out_path: Path,
    run_id: str,
    config_file_raw: Path,
    raw_run_instruction: str = "poetry run doit run --verbosity=2",
    get_pydoit_nb_run_command: GetPydoitNBRunCommandCallable | None = None,
) -> None:
    """
    Copy the README into the output bundle

    This is the default implementation. If you need other behaviour (for
    example, a different footer), write your own function then inject it as
    needed (e.g., into
    :func:`gen_copy_source_into_output_tasks`).

    Parameters
    ----------
    in_path
        Path to the raw README file (normally in the repository's root
        directory)

    out_path
        Path in which to write the README file (normally in the output bundle)

    run_id
        ID of the run. This is injected into the written README as part of the
        footer.

    config_file_raw
        Path to the raw configuration file, relative to the root output
        directory

    raw_run_instruction
        Instructions for how to run the workflow as they appear in the README.
        These are included to check that the instructions for running in the
        bundle are (likely) correct.

    get_pydoit_nb_run_command
        Callable that can create the run command to put in the pydoit-nb
        specific section of the copied README (this often differs from
        the command that is in the README to handle different paths,
        configuration files etc.).

    Raises
    ------
    AssertionError
        The run instructions in the README aren't as expected hence the code
        injection likely won't work as expected.

    ValueError
        ``config_file_raw`` is an absolute path. It should always be a relative
        path to ensure portability.
    """
    if get_pydoit_nb_run_command is None:
        get_pydoit_nb_run_command = get_pydoit_nb_run_command_default

    if config_file_raw.is_absolute():
        msg = f"``config_file_raw`` must be a relative path, received: {config_file_raw}"
        raise ValueError(msg)

    with open(in_path) as fh:
        raw = fh.read()

    if raw_run_instruction not in raw:
        msg = (
            "Could not find expected run instructions in README. "
            "The injected run instructions probably won't be correct. "
            f"Expected run instruction: {raw_run_instruction}"
        )
        raise AssertionError(msg)

    footer = f"""
## Pydoit info

This README was created from the raw {in_path.name} file as part of the {run_id!r} run with
[pydoit](https://pydoit.org/contents.html). The bundle should contain
everything required to reproduce the outputs. The environment can be
made with [poetry](https://python-poetry.org/) using the `poetry.lock` file
and the `pyproject.toml` file. Please disregard messages about the `Makefile`
in this file.

If you are looking to re-run the analysis, then you should run the below

```sh
{get_pydoit_nb_run_command(config_file_raw, raw_run_instruction)}
```

The reason for this is that you want to use the configuration with relative
paths. The configuration file that is included in this output bundle contains
absolute paths for reproducibility and traceability reasons. However, such
absolute paths are not portable so you need to use the configuration file
above, which is the raw configuration file as it was was used in the original
run.

If you have any issues running the analysis, please make an issue in our code
repository or reach out via email.
"""
    with open(out_path, "w") as fh:
        fh.write(raw)
        fh.write(footer)


def get_pydoit_nb_run_command_default(config_file_raw: Path, raw_run_instruction: str) -> str:
    """
    Get run command

    This is the default implementation, based on how we have typically set up
    our pydoit-nb based repositories.

    Parameters
    ----------
    config_file_raw
        Path to raw configuration file as it should be used in the run command

    raw_run_instruction
        The command to run the analysis in the README (before the pydoit
        specific instructions are added).

    Returns
    -------
        Run command for use in the pydoit-nb created bundle
    """
    return f"DOIT_CONFIGURATION_FILE={config_file_raw} {raw_run_instruction}"


def copy_zenodo_default(in_path: Path, out_path: Path, version: str) -> None:
    """
    Copy Zenodo JSON file to the output bundle

    This is the default implementation that updates the version information
    too. If you need other behaviour, write your own function then inject it as
    needed (e.g., into :func:`gen_copy_source_into_output_tasks`).

    More information about the metadata that can be uploaded via the zenodo
    API can be found under the "Deposit metadata" heading in the
    `zenodo API docs <https://developers.zenodo.org/#representation>`_.

    Parameters
    ----------
    in_path
        Path to raw Zenodo file

    out_path
        Path to output Zenodo file in the bundle

    version
        Version to write in the Zenodo file
    """
    with open(in_path) as fh:
        zenodo_metadata = json.load(fh)

    zenodo_metadata["metadata"]["version"] = version

    with open(out_path, "w") as fh:
        fh.write(json.dumps(zenodo_metadata, indent=2))


copy_file_default = swallow_output(shutil.copy2)

copy_tree_default = partial(
    shutil.copytree,
    ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
    dirs_exist_ok=True,
)

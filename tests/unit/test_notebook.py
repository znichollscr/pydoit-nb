"""
Test notebook module
"""
import json
import re
from pathlib import Path

import pytest
from attrs import define
from doit.tools import config_changed

from pydoit_nb.notebook import ConfiguredNotebook, UnconfiguredNotebook
from pydoit_nb.notebook_run import run_notebook
from pydoit_nb.testing import assert_doit_tasks_equal


@define
class Converter:
    def dumps(self, config, sort_keys):
        json.dumps(config, sort_keys=sort_keys)


@define
class ConfigChangedMock:
    dumps_output: str


def get_unconfigured(**kwargs):
    kwargs.setdefault("notebook_path", Path("/raw") / "notebook" / "path")
    kwargs.setdefault("raw_notebook_ext", ".py")
    kwargs.setdefault("summary", "Summary line")
    kwargs.setdefault("doc", "Docs go here.\nCan be multi-line.")

    return UnconfiguredNotebook(**kwargs)


def get_configured(unconfigured: UnconfiguredNotebook, **kwargs):
    kwargs.setdefault("configuration", (3.4, "a string"))
    kwargs.setdefault("dependencies", (Path("/path") / "to" / "dependency.csv",))
    kwargs.setdefault("targets", (Path("/path/to/output.nc"),))
    kwargs.setdefault("config_file", Path("/path") / "to" / "config.yaml")
    kwargs.setdefault("step_config_id", "sensitivity")

    return ConfiguredNotebook(unconfigured_notebook=unconfigured, **kwargs)


def get_base_task(**kwargs):
    kwargs.setdefault("basename", "base_task_name")
    kwargs.setdefault("doc", "base task docs\nhere")

    return kwargs


def test_to_doit_task():
    """
    Test conversion to a doit task

    This tests the combination of unconfigured and configured notebooks
    and the conversion to a doit task.

    This tests the most common path. It is probably an easier test to follow
    than the ones below so should be read first.
    """
    root_dir_raw_notebooks = Path("/path") / "to" / "raw-notebook"
    notebook_output_dir = Path("/path/to/notebook-output")
    clean = True

    unconfigured = get_unconfigured()
    configured = get_configured(unconfigured)
    base_task = get_base_task()
    converter = Converter()

    raw_notebook_exp = root_dir_raw_notebooks / unconfigured.notebook_path.with_suffix(
        unconfigured.raw_notebook_ext
    )
    dependencies_exp = [*configured.dependencies, raw_notebook_exp]
    has_config_changed_exp = ConfigChangedMock(converter.dumps(configured.configuration, sort_keys=True))
    exp = dict(
        basename=base_task["basename"],
        name=configured.step_config_id,
        doc=f"{base_task['doc']}. step_config_id={configured.step_config_id!r}",
        actions=[
            (
                run_notebook,
                [],
                {
                    "raw_notebook": raw_notebook_exp,
                    "unexecuted_notebook": notebook_output_dir
                    / f"{unconfigured.notebook_path.name}_unexecuted.ipynb",
                    "executed_notebook": notebook_output_dir / f"{unconfigured.notebook_path.name}.ipynb",
                    "notebook_parameters": dict(
                        config_file=str(configured.config_file),
                        step_config_id=configured.step_config_id,
                    ),
                },
            )
        ],
        targets=configured.targets,
        file_dep=dependencies_exp,
        clean=clean,
        uptodate=(has_config_changed_exp,),
    )

    res = configured.to_doit_task(
        root_dir_raw_notebooks=root_dir_raw_notebooks,
        notebook_output_dir=notebook_output_dir,
        base_task=base_task,
        converter=converter,
        clean=clean,
        config_changed_class=ConfigChangedMock,
    )

    assert res == exp


def test_to_doit_task_no_configuration():
    """
    Test behaviour if no configuration is specified for the configured notebook
    """
    root_dir_raw_notebooks = Path("/path") / "to" / "raw-notebook"
    notebook_output_dir = Path("/path/to/notebook-output")
    clean = True

    unconfigured = get_unconfigured()
    configured = get_configured(
        unconfigured,
        configuration=None,  # key difference from test above
    )
    base_task = get_base_task()
    converter = Converter()

    raw_notebook_exp = root_dir_raw_notebooks / unconfigured.notebook_path.with_suffix(
        unconfigured.raw_notebook_ext
    )
    dependencies_exp = [
        *configured.dependencies,
        raw_notebook_exp,
        configured.config_file,  # no configuration so entire config file becomes a dependency
    ]

    exp = dict(
        basename=base_task["basename"],
        name=configured.step_config_id,
        doc=f"{base_task['doc']}. step_config_id={configured.step_config_id!r}",
        actions=[
            (
                run_notebook,
                [],
                {
                    "raw_notebook": raw_notebook_exp,
                    "unexecuted_notebook": notebook_output_dir
                    / f"{unconfigured.notebook_path.name}_unexecuted.ipynb",
                    "executed_notebook": notebook_output_dir / f"{unconfigured.notebook_path.name}.ipynb",
                    "notebook_parameters": dict(
                        config_file=str(configured.config_file),
                        step_config_id=configured.step_config_id,
                    ),
                },
            )
        ],
        targets=configured.targets,
        file_dep=dependencies_exp,
        clean=clean,
    )

    res = configured.to_doit_task(
        root_dir_raw_notebooks=root_dir_raw_notebooks,
        notebook_output_dir=notebook_output_dir,
        base_task=base_task,
        converter=converter,
        clean=clean,
        config_changed_class=ConfigChangedMock,
    )

    assert res == exp


def test_to_doit_task_no_converter():
    error_msg = re.escape("If `self.configuration is not None` then `converter` must be supplied")
    with pytest.raises(ValueError, match=error_msg):
        get_configured(get_unconfigured()).to_doit_task(
            root_dir_raw_notebooks=Path("/somewhere"),
            notebook_output_dir=Path("/a/place"),
            base_task=get_base_task(),
        )


@pytest.mark.parametrize(
    [
        "dependencies",
        "targets",
        "clean",
        "basename",
        "base_task_doc",
        "root_dir_raw_notebooks",
        "notebook_output_dir",
        "unconfigured_notebook_path",
        "unconfigured_notebook_ext",
        "unconfigured_notebook_summary",
        "unconfigured_notebook_doc",
        "configuration",
        "step_config_id",
        "config_file",
    ],
    (
        pytest.param(
            (Path("/to") / "dependency.txt",),
            (Path("/to") / "target.csv",),
            True,
            "basename",
            "Base task\ndoc",
            Path("/path") / "to" / "raw-notebook",
            Path("/path/to/notebook-output"),
            Path("/to/unconfigured/notebook"),
            ".py",
            "Unconfigured notebook summary",
            "Unconfigured notebook\ndocs here",
            (33.3, "hi", "bye", "config"),
            "step_config_id",
            Path("/to") / "directory" / "with" / "config_file.yaml",
            id="base",
        ),
        pytest.param(
            (),
            (),
            False,
            "basename_two",
            "Base tasks\ndoc can go here for example",
            Path("/path") / "to" / "other-raw-notebook",
            Path("/to/notebook-output"),
            Path("/to/unc/notebook"),
            ".md",
            "Unconfigured notebook summary one linear",
            "Unconfigured notebook\ndocs here like\nthis for example",
            ("config",),
            "step_config_id_other",
            Path("/to") / "config_file.yaml",
            id="empty_values",
        ),
    ),
)
def test_to_doit_task_paths(  # noqa: PLR0913
    dependencies,
    targets,
    clean,
    basename,
    root_dir_raw_notebooks,
    notebook_output_dir,
    unconfigured_notebook_path,
    unconfigured_notebook_ext,
    unconfigured_notebook_summary,
    unconfigured_notebook_doc,
    configuration,
    step_config_id,
    base_task_doc,
    config_file,
):
    converter = Converter()

    raw_notebook_exp = root_dir_raw_notebooks / unconfigured_notebook_path.with_suffix(
        unconfigured_notebook_ext
    )
    dependencies_exp = [*dependencies, raw_notebook_exp]
    targets_exp = targets
    has_config_changed_exp = config_changed(converter.dumps(configuration, sort_keys=True))
    exp = dict(
        basename=basename,
        name=step_config_id,
        doc=f"{base_task_doc}. step_config_id={step_config_id!r}",
        actions=[
            (
                run_notebook,
                [],
                {
                    "raw_notebook": raw_notebook_exp,
                    "unexecuted_notebook": notebook_output_dir
                    / f"{unconfigured_notebook_path.name}_unexecuted.ipynb",
                    "executed_notebook": notebook_output_dir / f"{unconfigured_notebook_path.name}.ipynb",
                    "notebook_parameters": dict(
                        config_file=str(config_file),
                        step_config_id=step_config_id,
                    ),
                },
            )
        ],
        targets=targets_exp,
        file_dep=dependencies_exp,
        clean=clean,
        uptodate=(has_config_changed_exp,),
    )

    unconfigured = get_unconfigured(
        notebook_path=unconfigured_notebook_path,
        raw_notebook_ext=unconfigured_notebook_ext,
        summary=unconfigured_notebook_summary,
        doc=unconfigured_notebook_doc,
    )
    configured = get_configured(
        unconfigured,
        configuration=configuration,
        dependencies=dependencies,
        targets=targets,
        config_file=config_file,
        step_config_id=step_config_id,
    )
    base_task = get_base_task(basename=basename, doc=base_task_doc)

    res = configured.to_doit_task(
        root_dir_raw_notebooks=root_dir_raw_notebooks,
        notebook_output_dir=notebook_output_dir,
        base_task=base_task,
        converter=converter,
        clean=clean,
    )

    assert_doit_tasks_equal(res, exp)

"""
Test notebook_step module
"""
import inspect
import json
import re
from pathlib import Path

import pytest
from attrs import define, frozen
from doit.tools import config_changed

from pydoit_nb.config_handling import get_config_for_step_id
from pydoit_nb.notebook import ConfiguredNotebook, UnconfiguredNotebook
from pydoit_nb.notebook_run import run_notebook
from pydoit_nb.notebook_step import UnconfiguredNotebookBasedStep
from pydoit_nb.testing import assert_doit_tasks_equal


def test_workflow():
    """
    This test sets everything up inside the test to try and make it easier to follow

    Normally these pieces would be spread across multiple files in any application.
    """
    step_name = "plot"
    unconfigured_notebooks = (
        UnconfiguredNotebook(
            notebook_path=Path("notebook") / "plot-one",
            raw_notebook_ext=".py",
            summary="Some summary",
            doc="Some docs",
        ),
        UnconfiguredNotebook(
            notebook_path=Path("notebook") / "path-to" / "plot-two",
            raw_notebook_ext=".md",
            summary="Some summary here",
            doc="Some other docs",
        ),
    )

    def configure_notebooks(
        unconfigured_notebooks,
        config_bundle,
        step_name,
        step_config_id,
    ):
        config_step = get_config_for_step_id(
            config=config_bundle.config_hydrated,
            step=step_name,
            step_config_id=step_config_id,
        )

        res = []
        for nb in unconfigured_notebooks:
            configured = ConfiguredNotebook(
                unconfigured_notebook=nb,
                configuration=config_step.configurations[nb],
                dependencies=(config_step.dependencies[nb],),
                targets=(config_step.targets[nb],),
                config_file=config_bundle.config_hydrated_path,
                step_config_id=step_config_id,
            )

            res.append(configured)

        return res

    unconfigured_step = UnconfiguredNotebookBasedStep(
        step_name=step_name,
        unconfigured_notebooks=unconfigured_notebooks,
        configure_notebooks=configure_notebooks,
    )

    @frozen
    class PlotConfig:
        step_config_id: str
        dependencies: dict[UnconfiguredNotebook, Path]
        targets: dict[UnconfiguredNotebook, Path]
        configurations: dict[UnconfiguredNotebook, tuple[str, int]]

    @frozen
    class Config:
        plot: list[PlotConfig]

    @frozen
    class ConfigBundle:
        config_hydrated: Config
        """Hydrated config"""

        config_hydrated_path: Path
        """Path in/from which to read/write ``config_hydrated``"""

        root_dir_output_run: Path
        """Root output directory for this run"""

    @define
    class Converter:
        def dumps(self, config, sort_keys):
            json.dumps(config, sort_keys=sort_keys)

    root_dir_output_run = Path("Outputs") / "go" / "here"
    config_hydrated_path = root_dir_output_run / "config-hydrated.yaml"
    step_config_ids = ["default", "inverse"]
    identifiers = [(1, 2), (-1, -2)]
    config_hydrated = Config(
        [
            PlotConfig(
                step_config_id=step_config_id,
                dependencies={
                    nb: root_dir_output_run / "outputs" / f"results_{ids[i]}.csv"
                    for i, nb in enumerate(unconfigured_notebooks)
                },
                targets={
                    nb: root_dir_output_run / "outputs" / f"plot_{ids[i]}.pdf"
                    for i, nb in enumerate(unconfigured_notebooks)
                },
                configurations={nb: ("hi", i) for i, nb in enumerate(unconfigured_notebooks)},
            )
            for (step_config_id, ids) in zip(step_config_ids, identifiers)
        ],
    )
    config_bundle = ConfigBundle(
        config_hydrated=config_hydrated,
        config_hydrated_path=config_hydrated_path,
        root_dir_output_run=root_dir_output_run,
    )
    root_dir_raw_notebooks = Path("/root/dir/raw/notebooks")
    clean = False
    converter = Converter()

    assert inspect.isgeneratorfunction(unconfigured_step.gen_notebook_tasks)
    # Get results in a list to force the generator to empty (have all checked it is a
    # generator above).
    res = list(
        unconfigured_step.gen_notebook_tasks(
            config_bundle=config_bundle,
            root_dir_raw_notebooks=root_dir_raw_notebooks,
            converter=converter,
            clean=clean,
        )
    )

    ## Check results
    # Check that base tasks are returned first. These base tasks are important
    # to be able to see the different notebooks, separate from the notebook
    # with configuration (which seems to work best as a sub-task in pydoit-nb).
    base_tasks = {}
    for i, unconfigured_nb in enumerate(unconfigured_notebooks):
        assert res[i] == {
            "basename": f"({unconfigured_nb.notebook_path}) {unconfigured_nb.summary}",
            "name": None,
            "doc": unconfigured_nb.doc,
        }
        base_tasks[unconfigured_nb] = res[i]

    # Now check that all the notebooks are configured as intended for each different
    # step_config_id.
    for i, step_config_id in enumerate(step_config_ids):
        configured_notebooks = configure_notebooks(
            unconfigured_notebooks,
            config_bundle=config_bundle,
            step_name=step_name,
            step_config_id=step_config_id,
        )

        for j, configured_nb in enumerate(configured_notebooks):
            check_i = len(unconfigured_notebooks) + i * len(step_config_ids) + j
            notebook_output_dir_exp = root_dir_output_run / "notebooks-executed" / step_name / step_config_id

            # Each element in res is a doit task. Here we test their status
            # both via the to_doit_task API but also with a more hard-coded
            # approach (which is less sensitive to implementation details,
            # we'll probably get rid of one of these approaches at some point).
            # More thorough testing of the different ways to create tasks is
            # done elsewhere.
            exp = configured_nb.to_doit_task(
                root_dir_raw_notebooks=root_dir_raw_notebooks,
                notebook_output_dir=notebook_output_dir_exp,
                base_task=base_tasks[configured_nb.unconfigured_notebook],
                converter=converter,
                clean=clean,
            )

            assert_doit_tasks_equal(res[check_i], exp)

            raw_notebook = (
                root_dir_raw_notebooks
                / configured_nb.unconfigured_notebook.notebook_path.with_suffix(
                    configured_nb.unconfigured_notebook.raw_notebook_ext
                )
            )
            unexecuted_notebook = (
                notebook_output_dir_exp
                / f"{configured_nb.unconfigured_notebook.notebook_path.name}_unexecuted.ipynb"
            )
            executed_notebook = (
                notebook_output_dir_exp / f"{configured_nb.unconfigured_notebook.notebook_path.name}.ipynb"
            )

            exp_id = identifiers[i][j]

            assert_doit_tasks_equal(
                res[check_i],
                {
                    "basename": base_tasks[configured_nb.unconfigured_notebook]["basename"],
                    "name": step_config_id,
                    "doc": (
                        f"{configured_nb.unconfigured_notebook.doc}. " f"step_config_id={step_config_id!r}"
                    ),
                    "actions": [
                        (
                            run_notebook,
                            [],
                            {
                                "base_notebook": raw_notebook,
                                "unexecuted_notebook": unexecuted_notebook,
                                "executed_notebook": executed_notebook,
                                "notebook_parameters": {
                                    # Paths have to be passed as strings in the parameters
                                    "config_file": str(config_hydrated_path),
                                    "step_config_id": step_config_id,
                                },
                            },
                        )
                    ],
                    "targets": (root_dir_output_run / "outputs" / f"plot_{exp_id}.pdf",),
                    "file_dep": [
                        root_dir_output_run / "outputs" / f"results_{exp_id}.csv",
                        raw_notebook,
                    ],
                    "clean": clean,
                    "uptodate": (config_changed(converter.dumps(("hi", exp_id), sort_keys=True)),),
                },
            )

    assert check_i == len(res) - 1, "didn't test everything in res"


"""
Tests from here onwards use these defaults

This makes them harder to follow, but it is much easier to update single pieces
of them without having to duplicate code everywhere.
"""
DEFAULT_STEP_NAME = "process"
UNCONFIGURED_NOTEBOOKS_DEFAULT = (
    UnconfiguredNotebook(
        notebook_path=Path("/notebook") / "path",
        raw_notebook_ext=".py",
        summary="Some summary",
        doc="Some docs",
    ),
    UnconfiguredNotebook(
        notebook_path=Path("/notebook") / "path-to" / "elsewhere",
        raw_notebook_ext=".md",
        summary="Some summary here",
        doc="Some other docs",
    ),
)


def get_unconfigured_step(**kwargs) -> UnconfiguredNotebookBasedStep:
    def configure_notebooks(
        unconfigured_notebooks,
        config_bundle,
        step_name,
        step_config_id,
    ):
        config_step = get_config_for_step_id(
            config=config_bundle.config_hydrated,
            step=step_name,
            step_config_id=step_config_id,
        )

        res = []
        for nb in unconfigured_notebooks:
            configured = ConfiguredNotebook(
                unconfigured_notebook=nb,
                configuration=None,
                dependencies=(),
                targets=(config_step.targets[nb],),
                config_file=config_bundle.config_hydrated_path,
                step_config_id=step_config_id,
            )

            res.append(configured)

        return res

    kwargs.setdefault("step_name", DEFAULT_STEP_NAME)
    kwargs.setdefault("unconfigured_notebooks", UNCONFIGURED_NOTEBOOKS_DEFAULT)
    kwargs.setdefault("configure_notebooks", configure_notebooks)

    return UnconfiguredNotebookBasedStep(**kwargs)


@frozen
class ProcessConfig:
    step_config_id: str
    configs: dict[UnconfiguredNotebook, tuple[str, float]]
    targets: dict[UnconfiguredNotebook, Path]


@frozen
class Config:
    process: list[ProcessConfig]


def get_config_hydrated(**kwargs):
    kwargs.setdefault(
        DEFAULT_STEP_NAME,
        [
            ProcessConfig(
                step_config_id="default",
                configs={k: i for i, k in enumerate(UNCONFIGURED_NOTEBOOKS_DEFAULT)},
                targets={
                    k: Path("/to") / "outputs" / f"{i}.csv"
                    for i, k in enumerate(UNCONFIGURED_NOTEBOOKS_DEFAULT)
                },
            ),
            ProcessConfig(
                step_config_id="inverse",
                configs={k: -i for i, k in enumerate(UNCONFIGURED_NOTEBOOKS_DEFAULT)},
                targets={
                    k: Path("/to") / "outputs" / f"{-i}.csv"
                    for i, k in enumerate(UNCONFIGURED_NOTEBOOKS_DEFAULT)
                },
            ),
        ],
    )

    return Config(**kwargs)


@frozen
class ConfigBundle:
    config_hydrated: Config
    """Hydrated config"""

    config_hydrated_path: Path
    """Path in/from which to read/write ``config_hydrated``"""

    root_dir_output_run: Path
    """Root output directory for this run"""


def get_config_bundle(**kwargs):
    kwargs.setdefault(
        "config_hydrated",
        get_config_hydrated(**kwargs.pop("get_config_hydrated_kwargs", {})),
    )
    kwargs.setdefault("config_hydrated_path", Path("/to") / "run-output" / "config-hydrated.yaml")
    kwargs.setdefault("root_dir_output_run", Path("/to") / "run-output")

    return ConfigBundle(**kwargs)


def test_setup_runs_error_free():
    """Important check to make sure errors in downstream aren't because of errors in setup"""
    unconfigured_step = get_unconfigured_step()
    config_bundle = get_config_bundle()
    root_dir_raw_notebooks = Path("/root/dir/raw/notebooks")

    # Use list to force generator to empty
    list(
        unconfigured_step.gen_notebook_tasks(
            config_bundle=config_bundle,
            root_dir_raw_notebooks=root_dir_raw_notebooks,
        )
    )


def test_different_number_notebooks_raises():
    def configure_notebooks(
        unconfigured_notebooks,
        config_bundle,
        step_name,
        step_config_id,
    ):
        config_step = get_config_for_step_id(
            config=config_bundle.config_hydrated,
            step=step_name,
            step_config_id=step_config_id,
        )

        res = []
        for nb in unconfigured_notebooks[:-1]:  # Don't return config for all notebooks
            configured = ConfiguredNotebook(
                unconfigured_notebook=nb,
                configuration=(config_step.configs[nb],),
                dependencies=(),
                targets=(config_step.targets[nb],),
                config_file=config_bundle.config_hydrated_path,
                step_config_id=step_config_id,
            )

            res.append(configured)

        return res

    unconfigured_step = get_unconfigured_step(configure_notebooks=configure_notebooks)
    config_bundle = get_config_bundle()
    root_dir_raw_notebooks = Path("/root/dir/raw/notebooks")

    error_msg = re.escape(
        "The number of unconfigured and configured notebooks is not the same. "
        "We haven't yet thought through this use case. "
        "Please raise an issue at https://github.com/climate-resource/pydoit-nb to discuss."
    )
    with pytest.raises(NotImplementedError, match=error_msg):
        # Use list to force generator to empty
        list(
            unconfigured_step.gen_notebook_tasks(
                config_bundle=config_bundle,
                root_dir_raw_notebooks=root_dir_raw_notebooks,
            )
        )

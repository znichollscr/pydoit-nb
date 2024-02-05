"""
Re-usable tools for generating tasks
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, Protocol, TypeVar

from pydoit_nb.notebook_step import UnconfiguredNotebookBasedStep
from pydoit_nb.typing import ConfigBundleLike, Converter, DoitTaskSpec

C = TypeVar("C")
CB_contra = TypeVar("CB_contra", bound=ConfigBundleLike[Any], contravariant=True)


class StepDefiningModuleLike(Protocol[C, CB_contra]):
    """
    Class that behaves like a module which defines a notebook-based step
    """

    @property
    def step(self) -> UnconfiguredNotebookBasedStep[C, CB_contra]:
        """
        Step this module defines
        """
        ...  # pragma: no cover


def generate_all_tasks(
    config_bundle: ConfigBundleLike[C],
    root_dir_raw_notebooks: Path,
    converter: Converter,
    step_defining_modules: Iterable[StepDefiningModuleLike[C, ConfigBundleLike[C]]],
    gen_zenodo_bundle_task: Callable[[list[DoitTaskSpec]], DoitTaskSpec],
) -> Iterable[DoitTaskSpec]:
    """
    Generate all tasks in the workflow

    This is a helper function for a common pattern. You can obviously do
    whatever you want in your own projects as there is a lot of flexibility.

    Parameters
    ----------
    config_bundle
        Configuration bundle to use in task generation

    root_dir_raw_notebooks
        Directory in which raw notebooks are kept.

    converter
        Object that can serialize the configuration bundle's hydrated config

    step_defining_modules
        Modules that define notebook-based steps

    gen_zenodo_bundle_task
        Callable that takes all the proceeding tasks and returns a task for
        generating a bundle which can be uploaded to Zenodo.

    Yields
    ------
        :mod:`doit` tasks to run
    """
    notebook_tasks: list[DoitTaskSpec] = []
    for step_defining_module in step_defining_modules:
        for task in step_defining_module.step.gen_notebook_tasks(
            config_bundle=config_bundle,
            root_dir_raw_notebooks=root_dir_raw_notebooks,
            converter=converter,
        ):
            yield task
            notebook_tasks.append(task)

    yield gen_zenodo_bundle_task(notebook_tasks)

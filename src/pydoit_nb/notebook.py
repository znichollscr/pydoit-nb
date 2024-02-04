"""
Notebook defining classes
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import frozen
from doit.tools import config_changed  # type: ignore

from .notebook_run import run_notebook

if TYPE_CHECKING:
    from .typing import Converter, DoitTaskSpec

C = TypeVar("C")


@frozen
class UnconfiguredNotebook:
    """A notebook without any configuration"""

    notebook_path: Path
    """Path to notebook, relative to the raw notebook directory"""

    raw_notebook_ext: str
    """Extension for the raw notebook"""

    summary: str
    """One line summary of the notebook"""
    # TODO: validation?

    doc: str
    """Documentation of the notebook (can be longer than one line)"""


@frozen
class ConfiguredNotebook:
    """
    A configured notebook

    It might make sense to refactor this so has an UnconfiguredNotebook
    as one of its attributes rather than duplicatinng things. That would
    probably also make it clearer that a configured notebook is just the
    combination of an unconfigured notebook and the config we want to use
    with it.
    """

    unconfigured_notebook: UnconfiguredNotebook
    """
    The unconfigured notebook which should be combined with the configuration
    """

    dependencies: tuple[Path, ...]
    """Paths on which the notebook depends"""

    targets: tuple[Path, ...]
    """Paths which the notebook creates/controls"""

    config_file: Path
    """Path to the config file to use with the notebook"""

    step_config_id: str
    """`step_config_id` to use for this run of the notebook"""

    # Type hinting could be improved, but even attrs seems to just use Any
    # for the signature of `dumps` so I don't think it is worth diving down
    # that rabbit hole right now.
    configuration: tuple[Any, ...] | None = None
    """
    Configuration used by the notebook.

    If any of the configuration changes then the notebook will be triggered.

    If nothing is provided, then the notebook will be run whenever the
    configuration file driving the notebook is modified (i.e. the notebook will
    be re-run for any configuration change).
    """
    # TODO: It looks like this solves a problem that even the original authors
    # hadn't thought about because they just suggest using forget here
    # https://pydoit.org/cmd-other.html#forget (although they also talk about
    # non-file dependencies elsewhere so maybe these are just out of date docs)

    def to_doit_task(  # noqa: PLR0913
        self,
        root_dir_raw_notebooks: Path,
        notebook_output_dir: Path,
        base_task: DoitTaskSpec,
        converter: Converter | None = None,
        clean: bool = True,
        config_changed_class: Any = config_changed,
    ) -> DoitTaskSpec:
        """
        Convert to a :mod:`doit` task

        Parameters
        ----------
        root_dir_raw_notebooks
            Root directory in which the raw (not yet run) notebooks are kept

        notebook_output_dir
            Directory in which to write out the run notebook

        base_task
            Base task definition for this notebook step

        converter
            Converter to use to serialise configuration if needed.

        clean
            If we run `doit clean`, should the targets also be removed?

        config_changed_class
            Class to use for creating our object which can identify if config
            has changed or not. This should only need to be changed in very
            rare circumstances. The type hint is very vague because we don't
            want to repeat the pydoit API/logic here.

        Returns
        -------
            Task specification for use with :mod:`doit`

        Raises
        ------
        TypeError
            ``self.configuration is not None`` but ``converter is None``
        """
        raw_notebook = root_dir_raw_notebooks / self.unconfigured_notebook.notebook_path.with_suffix(
            self.unconfigured_notebook.raw_notebook_ext
        )

        notebook_name = self.unconfigured_notebook.notebook_path.name
        unexecuted_notebook = notebook_output_dir / f"{notebook_name}_unexecuted.ipynb"
        executed_notebook = notebook_output_dir / f"{notebook_name}.ipynb"

        dependencies = [
            *self.dependencies,
            raw_notebook,
        ]
        notebook_parameters = dict(config_file=str(self.config_file), step_config_id=self.step_config_id)

        targets = self.targets

        task = dict(
            basename=base_task["basename"],
            name=self.step_config_id,
            doc=f"{base_task['doc']}. step_config_id={self.step_config_id!r}",
            actions=[
                (
                    run_notebook,
                    [],
                    {
                        "base_notebook": raw_notebook,
                        "unexecuted_notebook": unexecuted_notebook,
                        "executed_notebook": executed_notebook,
                        "notebook_parameters": notebook_parameters,
                    },
                )
            ],
            targets=targets,
            file_dep=dependencies,
            clean=clean,
        )

        if self.configuration is None:
            # Run whenever config file changes
            task["file_dep"].extend([self.config_file])
        else:
            if converter is None:
                msg = "If `self.configuration is not None` then `converter` must be supplied"
                raise ValueError(msg)

            has_config_changed = config_changed_class(converter.dumps(self.configuration, sort_keys=True))

            task["uptodate"] = (has_config_changed,)

        return task

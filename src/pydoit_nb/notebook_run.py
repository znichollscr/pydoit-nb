"""
Notebook running
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Callable

import jupytext
import papermill

logger = logging.getLogger(__name__)


_PYTHON_ADD_NOTE_INTRODUCED: int = 11
"""Python3 minor version in which add_note was introduced"""


class NotebookExecutionException(Exception):
    """
    Raised when a notebook fails to execute for any reason
    """

    def __init__(self, exc: Exception, filename: Path):
        note = f"{filename} failed to execute. Original exception: {exc}"
        if sys.version_info[1] >= _PYTHON_ADD_NOTE_INTRODUCED:
            self.add_note(note)  # type: ignore # can be removed once we apply mypy with Python 3.11

        super().__init__(exc)


def rewrite_notebook_default(
    raw_notebook: Path,
    unexecuted_notebook: Path,
    fmt: str = "ipynb",
) -> None:
    """
    Re-write notebooks from raw to unexecuted

    This is our default implementation to use in :func:`run_notebook`.

    Parameters
    ----------
    raw_notebook
        Path from which to read the raw notebook

    unexecuted_notebook
        Path in which to write the unexecuted notebook

    fmt
        Format in which to write the unexecuted notebook
    """
    logger.info("Reading raw notebook with jupytext: %s", raw_notebook)
    notebook_jupytext = jupytext.read(raw_notebook)

    logger.info("Writing unexecuted notebook: %s", unexecuted_notebook)
    # TODO: consider whether this should be elsewhere
    unexecuted_notebook.parent.mkdir(parents=True, exist_ok=True)
    jupytext.write(
        notebook_jupytext,
        unexecuted_notebook,
        fmt=fmt,
    )


def run_notebook(  # noqa: PLR0913
    raw_notebook: Path,
    unexecuted_notebook: Path,
    executed_notebook: Path,
    notebook_parameters: dict[str, str] | None = None,
    notebook_rewriter: Callable[[Path, Path], None] | None = None,
    notebook_executor: Callable[[Path, Path, dict[str, Any]], Any] | None = None,
) -> None:
    """
    Run a notebook

    This loads the notebook ``base_notebook`` using jupytext, then writes it
    as an ``.ipynb`` file to ``unexecuted_notebook``. It then runs this
    unexecuted notebook with papermill, writing it to ``executed_notebook``.

    Parameters
    ----------
    raw_notebook
        Notebook from which to start

    unexecuted_notebook
        Where to write the unexecuted notebook

    executed_notebook
        Where to write the executed notebook

    notebook_parameters
        Parameters to pass to the target notebook

        These parameters will replace the contents of a cell tagged "parameters".
        See the
        `papermill documentation <https://papermill.readthedocs.io/en/latest/usage-parameterize.html#designate-parameters-for-a-cell>`_
        for more information about parameterizing a notebook.

    notebook_rewriter
        Function to use to re-write the raw notebooks as unexecuted notebooks
        that can be executed by `notebook_executor`. We use jupytext for this
        (specifically :func:`rewrite_notebook_default`) by default and you
        shouldn't need to change this.

    notebook_executor
        Function to use to execute the notebooks. We use `papermill.execute_notebook`
        for this by default and you shouldn't need to change this.
    """
    if notebook_parameters is None:
        notebook_parameters = {}

    if notebook_rewriter is None:
        notebook_rewriter = rewrite_notebook_default

    if notebook_executor is None:
        notebook_executor = papermill.execute_notebook

    notebook_rewriter(raw_notebook, unexecuted_notebook)

    try:
        if not executed_notebook.parent.exists():
            logger.info(
                "Creating directory (and any required parent directories): %s",
                executed_notebook.parent,
            )
            executed_notebook.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Executing notebook: %s", unexecuted_notebook)
        notebook_executor(
            unexecuted_notebook,
            executed_notebook,
            notebook_parameters,
        )

    except Exception as exc:
        raise NotebookExecutionException(exc, unexecuted_notebook) from exc

"""
Test notebook_run module
"""
import logging
import re
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from pydoit_nb.notebook_run import NotebookExecutionException, run_notebook

_PYTHON_ADD_NOTE_INTRODUCED: int = 11


@pytest.mark.parametrize(
    "notebook_parameters, notebook_parameters_exp",
    (
        pytest.param(None, {}, id="default"),
        pytest.param({"a": 3.4}, {"a": 3.4}, id="parameters_provided"),
    ),
)
@pytest.mark.parametrize(
    "executed_notebook",
    (
        pytest.param("executed_notebook.ipynb", id="parent_already_exists"),
        pytest.param(Path("executed") / "notebook.ipynb", id="parent_doesnt_exist"),
        pytest.param(Path("executed") / "subfolder" / "notebook.ipynb", id="parents_dont_exist"),
    ),
)
def test_run_notebook(notebook_parameters, notebook_parameters_exp, executed_notebook, tmp_path, caplog):
    caplog.set_level(logging.INFO)

    raw_notebook = Path("/Path") / "to" / "base_notebook"
    unexecuted_notebook = Path("/TO") / "unexecuted" / "notebook.ipynb"
    executed_notebook = tmp_path / executed_notebook
    check_executed_notebook_dir_created = not executed_notebook.parent.exists()

    call_kwargs = {}
    if notebook_parameters is not None:
        call_kwargs["notebook_parameters"] = notebook_parameters

    notebook_rewriter = Mock()
    notebook_executor = Mock()

    res = run_notebook(
        raw_notebook=raw_notebook,
        unexecuted_notebook=unexecuted_notebook,
        executed_notebook=executed_notebook,
        notebook_rewriter=notebook_rewriter,
        notebook_executor=notebook_executor,
        **call_kwargs,
    )

    assert notebook_rewriter.called_once_with(raw_notebook, unexecuted_notebook)
    assert notebook_executor.called_once_with(unexecuted_notebook, executed_notebook, notebook_parameters_exp)

    assert res is None

    assert caplog.records[-1].message == f"Executing notebook: {unexecuted_notebook}"
    assert caplog.records[-1].levelno == logging.INFO

    if check_executed_notebook_dir_created:
        assert executed_notebook.parent.is_dir()
        assert executed_notebook.parent.exists()

        assert (
            caplog.records[-2].message
            == f"Creating directory (and any required parent directories): {executed_notebook.parent}"
        )
        assert caplog.records[-2].levelno == logging.INFO

    else:
        assert len(caplog.records) == 1


def test_run_notebook_error(tmp_path):
    raw_notebook = Path("/Path") / "to" / "base_notebook"
    unexecuted_notebook = Path("/TO") / "unexecuted" / "notebook.ipynb"
    executed_notebook = tmp_path / "executed.ipynb"

    notebook_rewriter = Mock()
    original_exc = KeyError("Some info here")
    notebook_executor = Mock(side_effect=original_exc)

    error_msg = re.escape(str(original_exc))
    with pytest.raises(NotebookExecutionException, match=error_msg) as exc:
        run_notebook(
            raw_notebook=raw_notebook,
            unexecuted_notebook=unexecuted_notebook,
            executed_notebook=executed_notebook,
            notebook_rewriter=notebook_rewriter,
            notebook_executor=notebook_executor,
        )

    if sys.version_info[1] >= _PYTHON_ADD_NOTE_INTRODUCED:
        assert exc.value.__notes__ == [
            f"{unexecuted_notebook} failed to execute. Original exception: {original_exc}"
        ]


# integration test too to make sure defaults work (in different folder)

"""
Test notebook_run with actual notebook running
"""
import json

import pytest

from pydoit_nb.notebook_run import run_notebook


@pytest.mark.parametrize(
    "notebook_parameters, notebook_parameters_exp",
    (
        pytest.param(None, {"factor": 2.0}, id="default"),
        pytest.param({"factor": 2.3}, {"factor": 2.3}, id="parameter-injection"),
    ),
)
def test_notebook_run_integration(notebook_parameters, notebook_parameters_exp, tmp_path):
    call_kwargs = {}
    if notebook_parameters is not None:
        call_kwargs["notebook_parameters"] = notebook_parameters

    raw_notebook = tmp_path / "raw_notebook.py"
    unexecuted_notebook = tmp_path / "unexecuted.ipynb"
    executed_notebook = tmp_path / "executed.ipynb"
    base = 3.0

    with open(raw_notebook, "w") as fh:
        # Write content into raw notebook
        fh.write(
            """# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% editable=true slideshow={"slide_type": ""} tags=["parameters"]
factor = 2.0

# %%\n"""
        )
        fh.write(f"res = {base} * factor\n")
        fh.write('print(f"res={res:.3f}")\n')

    run_notebook(
        raw_notebook=raw_notebook,
        unexecuted_notebook=unexecuted_notebook,
        executed_notebook=executed_notebook,
        **call_kwargs,
    )

    with open(executed_notebook) as fh:
        executed_json = json.loads(fh.read())

    assert executed_json["cells"][-1]["outputs"] == [
        {
            "name": "stdout",
            "output_type": "stream",
            "text": [f"res={base * notebook_parameters_exp['factor']:.3f}\n"],
        }
    ]

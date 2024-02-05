"""
Utilities for displaying things, typically by printing
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydoit_nb.typing import DoitTaskSpec


def print_config(**kwargs: Any) -> None:
    """
    Print configuration

    Parameters
    ----------
    **kwargs
        Config to show
    """
    config_str = "\n".join([f"\t{k}: {v}" for k, v in kwargs.items()])
    print(f"Will run with the following config:\n{config_str}\n")


def gen_show_configuration_task(
    configuration_file: Path,
    run_id: str,
    root_dir_output: Path,
    root_dir_raw_notebooks: Path,
) -> DoitTaskSpec:
    """
    Generate a :mod:`doit` task that shows the configuration being used for the run

    Parameters
    ----------
    configuration_file
        Configuration file being used for the run

    run_id
        Run ID being used for the run

    root_dir_output
        Root directory in which the run's output will be saved

    root_dir_raw_notebooks
        Root directory from which the raw notebooks will be fetched

    Returns
    -------
        :mod:`doit` task that shows the configuration
    """
    return {
        "name": "Show configuration",
        "actions": [
            (
                print_config,
                [],
                dict(
                    configuration_file=configuration_file,
                    run_id=run_id,
                    root_dir_output=root_dir_output,
                    root_dir_raw_notebooks=root_dir_raw_notebooks,
                ),
            )
        ],
    }

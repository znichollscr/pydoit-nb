"""
Set seed notebook-based step definition

In modules like these, we define the notebook-based step and also
how to configure the step at runtime.

TODO: I don't love how much duplication there is across these modules
(particularly if you want to write all your docstrings and type hints).
However, I don't really know how to reduce it either. Templates could
work, but really feels like overkill (maybe this is that rare instance
where copy-paste is the right choice).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydoit_nb.config_handling import get_config_for_step_id
from pydoit_nb.notebook import ConfiguredNotebook, UnconfiguredNotebook
from pydoit_nb.notebook_step import UnconfiguredNotebookBasedStep

if TYPE_CHECKING:
    from collections.abc import Iterable

    from local_config import ConfigBundle


def _configure_notebooks(
    unconfigured_notebooks: Iterable[UnconfiguredNotebook],
    config_bundle: ConfigBundle,
    step_name: str,
    step_config_id: str,
) -> list[ConfiguredNotebook]:
    uc_nbs_dict = {nb.notebook_path: nb for nb in unconfigured_notebooks}

    config = config_bundle.config_hydrated

    config_step = get_config_for_step_id(config=config, step=step_name, step_config_id=step_config_id)

    common = dict(
        config_file=config_bundle.config_hydrated_path,
        step_config_id=step_config_id,
    )
    configured_notebooks = [
        ConfiguredNotebook(
            unconfigured_notebook=uc_nbs_dict[Path("001_set-seed")],
            configuration=(config_step.seed,),
            dependencies=(),
            targets=(config_step.file_seed,),
            **common,
        ),
    ]

    return configured_notebooks


step = UnconfiguredNotebookBasedStep(
    step_name="set_seed",
    unconfigured_notebooks=[
        UnconfiguredNotebook(
            notebook_path=Path("001_set-seed"),
            raw_notebook_ext=".py",
            summary="set seed",
            doc="Set the seed for our runs",
        ),
    ],
    configure_notebooks=_configure_notebooks,
)

"""
Example configuration for a project

Normally this would be split over multiple files, but we're trying to keep things slim here
"""
from __future__ import annotations

from functools import partial
from pathlib import Path

from attrs import field, frozen

import pydoit_nb.serialization
from pydoit_nb.attrs_helpers import make_attrs_validator_compatible_single_input
from pydoit_nb.config_helpers import (
    assert_path_exists,
    assert_path_is_absolute,
    assert_path_is_subdirectory_of_root_dir_output,
    assert_step_config_ids_are_unique,
)

converter_yaml = pydoit_nb.serialization.converter_yaml


@frozen
class SetSeedConfig:
    """Configuration for setting the seed"""

    step_config_id: str
    """ID for this configuration of the step"""

    seed: int
    """Seed"""

    file_seed: Path
    """File in which to write the seed"""


@frozen
class MakeDrawsConfig:
    """Configuration for making the draws"""

    step_config_id: str
    """ID for this configuration of the step"""

    factor: float
    """Scaling factor"""

    file_draws: Path
    """File in which to save the draws"""

    file_draws_scaled: Path
    """File in which to save the scaled draws"""


@frozen
class RetrieveDataConfig:
    """Configuration for retrieving the data"""

    step_config_id: str
    """ID for this configuration of the step"""

    source: str
    """Source"""

    file_raw_data: Path
    """File in which to save the raw data"""

    file_clean_data: Path
    """File in which to save the clean data"""


@frozen
class PlotConfig:
    """Configuration for plotting"""

    step_config_id: str
    """ID for this configuration of the step"""

    colour: str
    """Colour to use"""

    file_plot: Path
    """Path in which to save the plot"""


@frozen
class Config:
    name: str
    """Name of the configuration"""

    set_seed: list[SetSeedConfig] = field(
        validator=[make_attrs_validator_compatible_single_input(assert_step_config_ids_are_unique)]
    )
    """Configurations to use for setting the seed"""

    make_draws: list[MakeDrawsConfig] = field(
        validator=[make_attrs_validator_compatible_single_input(assert_step_config_ids_are_unique)]
    )
    """Configurations to use for making the draws"""

    retrieve_data: list[RetrieveDataConfig] = field(
        validator=[make_attrs_validator_compatible_single_input(assert_step_config_ids_are_unique)]
    )
    """Configurations to use for retrieving data"""

    plot: list[PlotConfig] = field(
        validator=[make_attrs_validator_compatible_single_input(assert_step_config_ids_are_unique)]
    )
    """Configurations to use for plotting"""


load_config_from_file = partial(
    pydoit_nb.serialization.load_config_from_file,
    target=Config,
    converter=converter_yaml,
)


@frozen  # using frozen makes the class hashable, which is handy
class ConfigBundle:
    """
    Configuration bundle

    Has all key components in one place
    """

    run_id: str
    """ID for the run"""

    config_hydrated: Config
    """Hydrated config"""

    config_hydrated_path: Path
    """Path in/from which to read/write ``config_hydrated``"""

    root_dir_output: Path = field(
        validator=[
            make_attrs_validator_compatible_single_input(assert_path_is_absolute),
            make_attrs_validator_compatible_single_input(assert_path_exists),
        ]
    )
    """Root output directory"""

    root_dir_output_run: Path = field(
        validator=[
            make_attrs_validator_compatible_single_input(assert_path_is_absolute),
            make_attrs_validator_compatible_single_input(assert_path_exists),
            assert_path_is_subdirectory_of_root_dir_output,
        ]
    )
    """Root output directory for this run"""

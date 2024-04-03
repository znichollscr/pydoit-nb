"""
Tools for working with configuration
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, TypeVar, cast, overload

import attrs
import numpy as np
from attrs import AttrsInstance, evolve, fields

from pydoit_nb.serialization import write_config_in_config_bundle_to_disk
from pydoit_nb.typing import ConfigBundleCreator, ConfigBundleLike, Converter, NotebookConfigLike

try:
    import pint

    HAS_PINT = True
except ImportError:  # pragma: no cover
    HAS_PINT = False

T = TypeVar("T")


def insert_path_prefix(config: AI, prefix: Path) -> AI:
    """
    Insert path prefix into config attributes

    This adds the prefix ``prefix`` to any attributes of ``config`` which are
    :obj:`Path`

    Parameters
    ----------
    config
        Config to update

    prefix
        Prefix to add to paths

    Returns
    -------
        Updated ``config``
    """
    config_attrs = fields(config.__class__)

    evolutions: dict[str, Any] = {}
    for attr in config_attrs:
        attr_name = attr.name
        attr_value = getattr(config, attr_name)

        if isinstance(attr_value, dict):
            evolutions[attr_name] = {
                update_attr_value(k, prefix): update_attr_value(v, prefix) for k, v in attr_value.items()
            }

        elif isinstance(attr_value, Iterable) and iterable_values_are_updatable(attr_value):
            evolutions[attr_name] = [update_attr_value(v, prefix) for v in attr_value]

        else:
            evolutions[attr_name] = update_attr_value(attr_value, prefix)

    return evolve(config, **evolutions)  # type: ignore # no idea why this fails


# TODO: test this by testing that a value
# which has a pint quantity as an attribute
# doesn't cause insert_path_prefix to explode.
def iterable_values_are_updatable(value: Iterable[Any]) -> bool:
    """
    Determine whether an iterable's values are updatable by :func:`insert_path_prefix`.

    Parameters
    ----------
    value
        Value to check.

    Returns
    -------
        ``True`` if ``value``'s elements can be updated by :func:``update_attr_value`,
        ``False`` otherwise.
    """
    to_check = [str, np.ndarray]
    if HAS_PINT:
        to_check.append(pint.UnitRegistry.Quantity)

    if isinstance(value, tuple(to_check)):
        return False

    return True


@overload
def update_attr_value(value: AttrsInstance, prefix: Path) -> AttrsInstance:
    ...  # pragma: no cover


@overload
def update_attr_value(value: Path, prefix: Path) -> Path:
    ...  # pragma: no cover


@overload
def update_attr_value(value: T, prefix: Path) -> T:
    ...  # pragma: no cover


def update_attr_value(value: AttrsInstance | Path | T, prefix: Path) -> AttrsInstance | Path | T:
    """
    Update the attribute value if it is :obj:`Path` to include the prefix

    The prefix is taken from the outer scope

    Parameters
    ----------
    value
        Value to update

    prefix
        Prefix to insert before paths if ``value`` is an instance of ``Path``

    Returns
    -------
        Updated value
    """
    if attrs.has(type(value)):
        return insert_path_prefix(cast(AttrsInstance, value), prefix)

    if isinstance(value, Path):
        return prefix / value

    return value


def get_step_config_ids(step_configs: Iterable[NotebookConfigLike]) -> list[str]:
    """
    Get available config IDs from an iterable of step configurations

    Parameters
    ----------
    step_configs
        Step configurations from which to retrieve the step config IDs

    Returns
    -------
        Step config ID from each step config in ``step_configs``

    Raises
    ------
    AttributeError
        Any object in ``step_configs`` is missing a `"step_config_id"` attribute.
    """
    attr_to_get = "step_config_id"
    try:
        res = [getattr(c, attr_to_get) for c in step_configs]
    except AttributeError as exc:
        # A bit of mucking around, but provides much more information in case
        # we hit this error.
        for c in step_configs:
            if not hasattr(c, attr_to_get):
                msg = f"{c!r} is missing a `{attr_to_get}` attribute"
                raise AttributeError(msg) from exc

        raise NotImplementedError("How did you get here") from exc  # pragma: no cover

    return res


def get_config_for_step_id(
    config: Any,
    step: str,
    step_config_id: str,
) -> Any:
    """
    Get configuration for a specific value of step config ID for a specific step

    This will fail if ``step`` isn't a part of ``config``

    Parameters
    ----------
    config
        Config from which to retrieve the step config

    step
        Step in ``config`` in which to find a step that has the a step config ID
        equal to ``step_config_id``

    step_config_id
        Value that the retrieved configuration's ``step_config_id`` must match

    Returns
    -------
        Configuration for step ``step`` in ``config`` with a step config ID
        equal to ``step_config_id``

    Raises
    ------
    ValueError
        No step could be found with ID equal to ``step_config_id``

    AttributeError
        ``config`` does not have a an attribute equal to the value given in
        ``step``
    """
    possibilities: Iterable[NotebookConfigLike] = getattr(config, step)
    available_step_config_ids = []
    for poss in possibilities:
        if poss.step_config_id == step_config_id:
            return poss
        else:
            available_step_config_ids.append(poss.step_config_id)

    raise ValueError(  # noqa: TRY003
        f"Couldn't find {step_config_id=} for {step=}. "
        f"Available step config IDs: {available_step_config_ids}"
    )


AI = TypeVar("AI", bound=AttrsInstance)
CB = TypeVar("CB", bound=ConfigBundleLike[Any])


def load_hydrate_write_config_bundle(
    configuration_file: Path,
    load_configuration_file: Callable[[Path], AI],
    create_config_bundle: ConfigBundleCreator[AI, CB],
    root_dir_output_run: Path,
    converter: Converter,
) -> CB:
    """
    Load, hydrate and write (to disk) :obj:`ConfigBundleLike`

    Parameters
    ----------
    configuration_file
        File from which to load the configuration

    load_configuration_file
        Callable to use to load the configuration from a file

    create_config_bundle
        Callable to use to create the :obj:`ConfigBundleLike` from the
        loaded configuration, the path in which the hydrated config will
        be written and the run's output root directory.

    root_dir_output_run
        Root directory in which to write output for this run

    converter
        Converter to use to serialise the output :obj:`ConfigBundleLike` to
        disk

    Returns
    -------
        Loaded :obj:`ConfigBundleLike`
    """
    config = load_configuration_file(configuration_file)
    config = insert_path_prefix(config, prefix=root_dir_output_run)
    config_bundle = create_config_bundle(
        config_hydrated=config,
        config_hydrated_path=root_dir_output_run / configuration_file.name,
        root_dir_output_run=root_dir_output_run,
    )
    write_config_in_config_bundle_to_disk(config_bundle=config_bundle, converter=converter)

    return config_bundle

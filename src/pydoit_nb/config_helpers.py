"""
Helper functions that can be useful when setting up config
"""
from __future__ import annotations

import collections
from collections.abc import Collection
from pathlib import Path
from typing import TYPE_CHECKING

from pydoit_nb.config_handling import get_step_config_ids
from pydoit_nb.typing import NotebookConfigLike

if TYPE_CHECKING:
    from typing import Any

    import attr


def assert_path_exists(inp: Path) -> None:
    """
    Assert that a path exists

    Parameters
    ----------
    inp
        Path to check

    Raises
    ------
    FileNotFoundError
        ``inp`` does not exist
    """
    if not inp.exists():
        raise FileNotFoundError(f"{inp} does not exist")  # noqa: TRY003


def assert_path_is_absolute(inp: Path) -> None:
    """
    Assert that a path is an absolute path

    Parameters
    ----------
    inp
        Path to check

    Raises
    ------
    AssertionError
        ``inp`` is not absolute
    """
    if not inp.is_absolute():
        raise AssertionError(f"{inp} is not absolute")  # noqa: TRY003


def assert_step_config_ids_are_unique(inp: Collection[NotebookConfigLike]) -> None:
    """
    Assert that all the :attr:`step_config_id` in a collection are unique

    Parameters
    ----------
    inp
        Collection of :obj:`NotebookConfigLike` objects to check.

    Raises
    ------
    AssertionError
        The :attr:`step_config_id` of each :obj:`NotebookConfigLike` are not unique.
    """
    step_config_ids = get_step_config_ids(inp)

    if len(set(step_config_ids)) != len(inp):
        duplicates = [id for id, count in collections.Counter(step_config_ids).items() if count > 1]

        msg = (
            "``step_config_id`` must be unique. "
            f"The following ``step_config_id`` are duplicated: {duplicates}"
        )
        raise AssertionError(msg)


def assert_path_is_subdirectory_of_root_dir_output(
    instance: Any, attribute: attr.Attribute[Any], value: Path
) -> None:
    """
    Assert that a path is a sub-directory of ``instance.root_dir_output``

    Parameters
    ----------
    instance
        Instance to check

    attribute
        Attribute that is being set

    value
        Value that is being used to set the attribute

    Raises
    ------
    AssertionError
        ``value`` is not a sub-directory of ``instance.root_dir_output``
    """
    if not value.is_relative_to(instance.root_dir_output):
        msg = (
            f"{attribute} is not a sub-directory of root_dir_output. "
            f"{attribute}={value}. root_dir_output={instance.root_dir_output!r}"
        )
        raise AssertionError(msg)

"""
Test config_helpers module
"""
import re
from pathlib import Path
from unittest.mock import Mock

import pytest

from pydoit_nb.attrs_helpers import AttributeInitialisationError
from pydoit_nb.config_helpers import (
    assert_path_exists,
    assert_path_is_absolute,
    assert_path_is_subdirectory_of_root_dir_output,
    assert_step_config_ids_are_unique,
)


def test_assert_path_exists(tmp_path):
    # no error
    assert_path_exists(tmp_path)

    with pytest.raises(FileNotFoundError):
        assert_path_exists(tmp_path / "junk.txt")


def test_assert_path_is_absolute(tmp_path):
    # no error
    assert_path_is_absolute(tmp_path)

    error_msg = f"{tmp_path.relative_to(tmp_path.parent.parent)} is not absolute"
    with pytest.raises(AssertionError, match=error_msg):
        assert_path_is_absolute(tmp_path.relative_to(tmp_path.parent.parent))


def test_assert_step_config_ids_are_unique():
    step_1 = Mock()
    step_1.step_config_id = "1"

    step_2 = Mock()
    step_2.step_config_id = "2"

    step_3 = Mock()
    step_3.step_config_id = "3"

    # no error
    assert_step_config_ids_are_unique([step_1, step_2, step_3])

    error_msg = re.escape(
        "``step_config_id`` must be unique. The following ``step_config_id`` are duplicated: ['2']"
    )
    with pytest.raises(AssertionError, match=error_msg):
        assert_step_config_ids_are_unique([step_1, step_2, step_2, step_3])


def test_assert_path_is_subdirectory_of_root_dir_output():
    root_dir_output = Path("/root") / "dir" / "output"
    somewhere_else = Path("/somewhere") / "else"

    instance = Mock()
    instance.root_dir_output = root_dir_output

    attribute = Mock()
    attribute.name = "output_dir_run"

    # No error
    assert_path_is_subdirectory_of_root_dir_output(instance, attribute, root_dir_output / "sub-dir")

    with pytest.raises(AttributeInitialisationError) as exc:
        assert_path_is_subdirectory_of_root_dir_output(instance, attribute, somewhere_else)

    error_msg = (
        f"``{attribute.name}`` is not a sub-directory of root_dir_output. "
        f"{attribute.name}={somewhere_else!r}. root_dir_output={instance.root_dir_output!r}"
    )
    assert isinstance(exc.value.__cause__, AssertionError)
    assert str(exc.value.__cause__) == error_msg

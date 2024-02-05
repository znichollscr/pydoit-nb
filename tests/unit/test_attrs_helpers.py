"""
Test attrs_helpers module
"""
import re
from unittest.mock import Mock

import pytest

from pydoit_nb.attrs_helpers import AttributeInitialisationError, make_attrs_validator_compatible_single_input


def test_make_attrs_validator_compatible_single_input():
    def func(inp: str) -> None:
        if inp != "hi":
            raise ValueError(f"inp must be hi, received: {inp}")

    wrapped = make_attrs_validator_compatible_single_input(func)

    instance = Mock()
    attribute = Mock()
    attribute.name = "attribute_name"
    # No error
    wrapped(instance, attribute, "hi")

    # Error
    error_msg = re.escape(
        "Error raised while initialising attribute "
        f"``attribute_name`` of ``{type(instance)}``. "
        "Value provided: bye"
    )
    with pytest.raises(AttributeInitialisationError, match=error_msg) as exc:
        wrapped(instance, attribute, "bye")

    assert isinstance(exc.value.__cause__, ValueError)
    assert str(exc.value.__cause__) == "inp must be hi, received: bye"

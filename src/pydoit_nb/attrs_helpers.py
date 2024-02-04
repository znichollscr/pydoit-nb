"""
Tools for helping with :mod:`attrs`, particularly validators

TODO: move this into its own package and check with attrs developers
if they want something like this in their package
"""
from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, TypeVar

    import attr

    T = TypeVar("T")


def add_attrs_context(
    original: Callable[[Any, attr.Attribute[Any], T], None],
) -> Callable[[Any, attr.Attribute[Any], T], None]:
    """
    Decorate function with a ``try...except`` to add the :mod:`attrs` context

    This means that the information about what attribute was being set and
    what value it was passed is also shown to the user

    Parameters
    ----------
    original
        Function to decorate

    Returns
    -------
        Decorated function

    Notes
    -----
    Only works with Python 3.11 and above. For other Python versions, the raw
    error is simply shown instead
    """

    @wraps(original)
    def with_attrs_context(
        instance: Any,
        attribute: attr.Attribute[Any],
        value: T,
    ) -> None:
        try:
            original(instance, attribute, value)
        except Exception as exc:
            if hasattr(exc, "add_note"):
                exc.add_note(
                    "\nError raised while initialising attribute "
                    f"``{attribute.name}`` of ``{type(instance)}``. "
                    f"\nValue provided: {value}"
                )

            raise

    return with_attrs_context


def make_attrs_validator_compatible_single_input(
    func_to_wrap: Callable[[T], None],
) -> Callable[[Any, attr.Attribute[Any], T], None]:
    """
    Create a function that is compatible with validation via :func:`attrs.field`

    This assumes that the function you're wrapping only takes a single input.

    Parameters
    ----------
    func_to_wrap
        Function to wrap

    Returns
    -------
        Wrapped function, which can be used as a validator with
        :func:`attrs.field`
    """

    @add_attrs_context
    @wraps(func_to_wrap)
    def attrs_compatible(
        instance: Any,
        attribute: attr.Attribute[Any],
        value: T,
    ) -> None:
        func_to_wrap(value)

    return attrs_compatible

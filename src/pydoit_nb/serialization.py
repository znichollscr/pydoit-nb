"""
Serialization tools

This module includes a default yaml converter. This may be exactly what you
need for your use case. If it isn't, the code will help you see how to set up
and customise a converter. This example, along with the cattrs docs, should
help you get going. We mainly use :func:`cattrs.register_structure_hook_func`
and :func:`cattrs.register_unstructure_hook_func` (see also
`here <https://catt.rs/en/stable/cattrs.html#cattrs.BaseConverter.register_structure_hook_func>`_
), which aren't as heavily documented, but are what we want. You may find
the other examples in
`the docs on customisation <https://catt.rs/en/stable/customizing.html#customizing-class-un-structuring>`_
more helpful.

One example of something we don't support well is preservation of data types
when structuring and unstructuring pint types. This is just a complicated
problem to do with type hinting. For most applications, we have found that the
default numpy data type is fine (everything becomes float64, which is generally
fine).

One other clear example of something we don't support here is structuring and
unstructuring pandas objects as yaml. The reason is that we can't see an easy
way to get the round-tripping to work in edge cases related to index naming and
data type preservation. There are ways to solve this problem, but they require
more care and time than we can put in right now. As two suggestions for
possible solutions: 1) use a back-end that isn't yaml 2) store information
about index types etc. in addition to the data frame (pandas itself doesn't do
this though, which makes us a bit nervous about how hard it could be to do in
the general case, although specific use cases should be far more tractable and
easy to test). If you'd like to discuss this more, please raise an issue.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypeVar, Union, cast

import cattrs.preconf.pyyaml
import numpy as np
import numpy.typing as nptype

from .typing import ConfigBundleLike, Converter

try:
    from typing_extensions import TypeAlias
except ImportError:  # >= python 3.11
    # remove type ignore when mypy applied with python 3.11
    from typing import TypeAlias  # type: ignore

try:
    import pint

    HAS_PINT = True
except ImportError:  # pragma: no cover
    HAS_PINT = False

T = TypeVar("T")
U = TypeVar("U")
N = TypeVar("N", bound=nptype.NDArray[Union[np.floating[Any], np.integer[Any]]])


def write_config_in_config_bundle_to_disk(
    config_bundle: ConfigBundleLike[U],
    converter: Converter[U],
) -> Path:
    """
    Write the configuration in a configuration bundle to disk

    The configuration is written in the path specified by
    ``config_bundle.config_hydrated_path``

    Parameters
    ----------
    config_bundle
        Configuration bundle to write to disk

    converter
        Object that can serialize the configuration bundle's hydrated config

    Returns
    -------
        Path in which ``config_bundle.config_hydrated`` was written
    """
    write_path = config_bundle.config_hydrated_path
    with open(write_path, "w") as fh:
        fh.write(converter.dumps(config_bundle.config_hydrated))

    return write_path


def load_config_from_file(config_file: Path, target: type[T], converter: Converter[U]) -> T:
    """
    Load configuration from file

    Parameters
    ----------
    config_file
        File from which to load configuration

    target
        Class to load

    converter
        Converter to use to convert from ``config_file``'s contents to an
        instance of ``target``

    Returns
    -------
        Loaded instance of ``target``
    """
    with open(config_file) as fh:
        config = converter.loads(fh.read(), target)

    return config


converter_yaml = cattrs.preconf.pyyaml.make_converter()


UnstructuredArray: TypeAlias = Union[Sequence[Union[int, float]], Sequence["UnstructuredArray"]]


def unstructure_np_array(arr: nptype.NDArray[np.float64]) -> UnstructuredArray:
    """
    Unstructure :obj:`npt.ArrayLike`

    This simply converts it to a list so is probably not very fast. However,
    this is just an example so could easily be optimised for production use if
    needed.

    Parameters
    ----------
    arr
        Array to unstructure

    Returns
    -------
        Unstructured array
    """
    return cast(UnstructuredArray, arr.tolist())


def structure_np_array(inp: UnstructuredArray, target_type: type[N]) -> N:
    """
    Structure :obj:`npt.ArrayLke`

    The inverse of :func:`unstructure_np_array`

    Parameters
    ----------
    inp
        Data to structure

    target_type
        Type the data should be returned as

    Returns
    -------
        Structured array
    """
    # Can't get mypy to behave, hence type ignore comments throughout here
    # TODO: push docs PR up into cattrs
    # See https://github.com/python-attrs/cattrs/issues/194#issuecomment-987341893
    target_dtype = target_type.__args__[1].__args__[0]  # type: ignore

    return np.array([target_dtype(row) for row in inp])  # type: ignore


def _is_np_array(inp: Any) -> bool:
    return inp is np.ndarray or (getattr(inp, "__origin__", None) is np.ndarray)


converter_yaml.register_unstructure_hook_func(_is_np_array, unstructure_np_array)
converter_yaml.register_structure_hook_func(_is_np_array, structure_np_array)


def unstructure_np_scalar(number: np.number[Any]) -> float | int:
    """
    Unstructure :obj:`np.number`

    This simply converts to a primative type.

    Parameters
    ----------
    number
        Number to unstructure

    Returns
    -------
        Unstructured number
    """
    if isinstance(number, np.floating):
        return float(number)

    return int(number)


def structure_np_scalar(inp: float | int, target_type: type[T]) -> T:
    """
    Structure :obj:`np.number`

    The inverse of :func:`unstructure_np_array`

    Parameters
    ----------
    inp
        Data to structure

    target_type
        Type the data should be returned as

    Returns
    -------
        Structured number
    """
    # Can't get mypy to behave here either
    return target_type(inp)  # type: ignore


def _is_np_scalar(inp: Any) -> bool:
    return issubclass(inp, np.number)


converter_yaml.register_unstructure_hook_func(_is_np_scalar, unstructure_np_scalar)
converter_yaml.register_structure_hook_func(_is_np_scalar, structure_np_scalar)

if HAS_PINT:
    UnstructuredPint: TypeAlias = Union[tuple[Union[int, float], str], tuple[UnstructuredArray, str]]

    def unstructure_pint(inp: pint.UnitRegistry.Quantity) -> UnstructuredPint:
        """
        Unstructure a :mod:`pint` quantity.

        Parameters
        ----------
        inp
            :obj:`pint.UnitRegistry.Quantity` to unstructure

        Returns
        -------
            Unstructured :obj:`pint.UnitRegistry.Quantity`
        """
        if _is_np_scalar(type(inp.magnitude)):
            return (unstructure_np_scalar(inp.magnitude), str(inp.units))

        if isinstance(inp.magnitude, float):
            return (inp.magnitude, str(inp.units))

        return (unstructure_np_array(inp.magnitude), str(inp.units))

    def structure_pint(
        inp: UnstructuredPint, target_type: type[pint.UnitRegistry.Quantity]
    ) -> pint.UnitRegistry.Quantity:
        """
        Structure :obj:`pint.UnitRegistry.Quantity`

        Parameters
        ----------
        inp
            Unstructured data

        target_type
            Type to create

        Returns
        -------
            Structured :obj:`pint.UnitRegistry.Quantity`
        """
        # pint not playing nice with mypy
        ur = pint.get_application_registry()  # type: ignore

        # Can't do dtype control until pint allows it again with e.g.
        # pint.Quantity[np.array[np.float64]]
        return ur.Quantity(np.array(inp[0]), inp[1])  # type: ignore

    def _is_pint(inp: Any) -> bool:
        # I don't love this way of checking, but I couldn't work out how to else to make it work
        return hasattr(inp, "units") & hasattr(inp, "magnitude") & ("pint" in str(inp))

    converter_yaml.register_unstructure_hook_func(_is_pint, unstructure_pint)
    converter_yaml.register_structure_hook_func(_is_pint, structure_pint)

else:  # pragma: no cover
    # TODO: decide whether lack of pint should raise a warning or not
    pass

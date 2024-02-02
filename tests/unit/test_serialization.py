"""
Test the serialization module
"""
from pathlib import Path

import numpy as np
import numpy.testing as nptesting
import numpy.typing as nptype
import pandas as pd
import pint
import pint.testing as pinttesting
import pytest
from attrs import define

from pydoit_nb.serialization import (
    converter_yaml,
    load_config_from_file,
    write_config_in_config_bundle_to_disk,
)

UR = pint.get_application_registry()


def test_write_load_config(tmp_path):
    """Test use of write_config_in_config_bundle_to_disk and load_config_from_file"""

    @define
    class Config:
        scaling: float
        id: str

    @define
    class ConfigBundle:
        config_hydrated_path: Path
        config_hydrated: Config

    start = ConfigBundle(tmp_path / "hydrated.yaml", Config(32.2, "test"))

    written_file = write_config_in_config_bundle_to_disk(
        config_bundle=start,
        converter=converter_yaml,
    )

    with open(written_file) as fh:
        written_raw = fh.read()

    assert written_raw == "id: test\nscaling: 32.2\n"

    res = load_config_from_file(
        written_file,
        target=Config,
        converter=converter_yaml,
    )

    assert res == start.config_hydrated


@pytest.mark.parametrize(
    "inp, exp, restructure_type",
    (
        pytest.param(
            {"key": Path("/path") / "to" / "somewhere.txt"},
            f"key: {Path('/path') / 'to' / 'somewhere.txt'!s}\n",
            dict[str, Path],
            id="Path",
        ),
        pytest.param(
            {"key": np.array([1, 3, 4])},
            "key:\n- 1\n- 3\n- 4\n",
            dict[str, nptype.NDArray[np.int64]],
            id="numpy_int64_array",
        ),
        pytest.param(
            {"key": np.array([1.2, 3.13, 4.45])},
            "key:\n- 1.2\n- 3.13\n- 4.45\n",
            dict[str, nptype.NDArray[np.float64]],
            id="numpy_float64_array",
        ),
        pytest.param(
            {"key": np.float64(1.2)},
            "key: 1.2\n",
            dict[str, np.float64],
            id="numpy_float64_scalar",
        ),
        pytest.param(
            {"key": np.int64(1)},
            "key: 1\n",
            dict[str, np.int64],
            id="numpy_int64_scalar",
        ),
        pytest.param(
            {"key": UR.Quantity(3.23, "kg")},
            "key:\n- 3.23\n- kilogram\n",
            dict[str, UR.Quantity],
            id="pint_scalar",
            marks=[pytest.mark.xfail(reason="No dtype preservation with pint yet")],
        ),
        pytest.param(
            {"key": UR.Quantity(np.float64(3.23), "kg")},
            "key:\n- 3.23\n- kilogram\n",
            dict[str, UR.Quantity],
            id="pint_float64_scalar",
        ),
        pytest.param(
            {"key": UR.Quantity(np.array([1.2, 3.13, 4.45]), "m")},
            "key:\n- - 1.2\n  - 3.13\n  - 4.45\n- meter\n",
            dict[str, UR.Quantity],
            id="pint_float64_array",
        ),
        pytest.param(
            {"key": UR.Quantity(np.array([1.2, 3.13, 4.45]).astype(np.float32), "m")},
            "key:\n- - 1.2000000476837158\n  - 3.130000114440918\n  - 4.449999809265137\n- meter\n",
            dict[str, UR.Quantity],
            id="pint_float32_array",
            marks=[pytest.mark.xfail(reason="Precision flaky and no dtype preservation with pint yet")],
        ),
        pytest.param(
            {"key": pd.Series([1.1, 3.3, 4.4])},
            "key:\n- 1.1\n- 3.3\n- 4.4\n",
            "Not thought through",
            id="pandas_series",
            marks=[pytest.mark.xfail(reason="pandas not supported yet")],
        ),
        pytest.param(
            {
                "key": pd.Series(
                    [210.5, 200.3, 120.3],
                    index=pd.Index([2010, 2011, 2020], name="year"),
                )
            },
            "Not thought through",
            dict[str, pd.Series],
            id="pandas_series_named_index",
            marks=[pytest.mark.xfail(reason="pandas not supported yet")],
        ),
        pytest.param(
            {
                "key": pd.DataFrame(
                    [210.5, 200.3, 120.3],
                    index=pd.Index([2010, 2011, 2020], name="year"),
                )
            },
            "Not thought through",
            dict[str, pd.DataFrame],
            id="pandas_df_named_index",
            marks=[pytest.mark.xfail(reason="pandas not supported yet")],
        ),
        pytest.param(
            {
                "key": pd.DataFrame([[1.1, 3.3, 4.4], [2.2, 6.6, 7.7]]),
            },
            "Not thought through",
            dict[str, pd.DataFrame],
            id="pandas_df_2D",
            marks=[pytest.mark.xfail(reason="pandas not supported yet")],
        ),
        # etc. for pandas tests, checking index names and dtypes, column
        # names and dtypes, multi-dimensional, multi-index etc.
    ),
)
def test_structure_non_primatives(inp, exp, restructure_type):
    res = converter_yaml.dumps(inp)
    assert res == exp

    roundtrip = converter_yaml.loads(res, restructure_type)
    assert_roundtrip_success(roundtrip, inp)


def assert_roundtrip_success(roundtrip_res, inp):
    if isinstance(inp, dict):
        for k, value in inp.items():
            assert_roundtrip_success(roundtrip_res[k], value)

        return

    if isinstance(inp, np.ndarray):
        nptesting.assert_equal(inp, roundtrip_res)
        assert inp.dtype == roundtrip_res.dtype
        return

    if isinstance(inp, pint.UnitRegistry.Quantity):
        pinttesting.assert_equal(inp, roundtrip_res)
        if hasattr(inp.m, "dtype"):
            assert inp.m.dtype == roundtrip_res.m.dtype
        else:
            isinstance(inp.m, roundtrip_res.m)

        return

    assert roundtrip_res == inp

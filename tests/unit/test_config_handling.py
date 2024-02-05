"""
Test config_handling
"""
from __future__ import annotations

import re
from functools import partial
from pathlib import Path

import pytest
from attrs import define

from pydoit_nb.config_handling import (
    get_config_for_step_id,
    get_step_config_ids,
    load_hydrate_write_config_bundle,
    update_attr_value,
)
from pydoit_nb.serialization import converter_yaml, load_config_from_file


@define
class StepConfigA:
    step_config_id: str
    other: str


@define
class StepConfigB:
    step_config_id: str
    helper: float


@define
class StepConfigC:
    step_config_id: str
    helper: float
    output: Path
    config: dict[str, str]


@define
class ConfigA:
    step_a: list[StepConfigA]
    step_b: list[StepConfigB]


@define
class ConfigB:
    step_c: list[StepConfigC]


@define
class ConfigBundleA:
    config_hydrated: ConfigB
    config_hydrated_path: Path
    root_dir_output_run: Path
    run_id: str


def test_get_step_config_ids():
    config_id_1 = "only"
    config_id_2 = "jitter"
    config_id_3 = "hitter"
    objs = [
        StepConfigA(config_id_1, "abc"),
        StepConfigA(config_id_2, "daef"),
        StepConfigB(config_id_3, 12.4),
    ]
    exp = [config_id_1, config_id_2, config_id_3]
    res = get_step_config_ids(objs)

    assert res == exp


@pytest.mark.parametrize(
    "vals, exp_failure",
    (
        pytest.param(["val"], "val", id="single_val"),
        pytest.param([StepConfigA("id", "other"), "val"], "val", id="single_val"),
    ),
)
def test_get_step_config_ids_attribute_error(vals, exp_failure):
    error_msg = re.escape(f"{exp_failure!r} is missing a `step_config_id` attribute")
    with pytest.raises(AttributeError, match=error_msg):
        get_step_config_ids(vals)


def test_get_config_for_step_id():
    target_id = "main"
    exp = StepConfigA(target_id, "other")
    config = ConfigA(
        step_a=[StepConfigA("junk", "junka"), exp, StepConfigA("junky", "joker")],
        step_b=[StepConfigB("hello", 3.1)],
    )

    res = get_config_for_step_id(config, step="step_a", step_config_id=target_id)

    assert res == exp


def test_get_config_for_step_id_value_error():
    config = ConfigA(
        step_a=[StepConfigA("name", "value"), StepConfigA("junk", "junka")],
        step_b=[StepConfigB("hello", 3.1)],
    )

    step = "step_a"
    step_config_id = "gnome"
    possible_ids = [step.step_config_id for step in getattr(config, step)]

    error_msg = re.escape(
        f"Couldn't find {step_config_id=} for {step=}. " f"Available step config IDs: {possible_ids}"
    )
    with pytest.raises(ValueError, match=error_msg):
        get_config_for_step_id(config, step="step_a", step_config_id="gnome")


def test_get_config_for_step_id_attribute_error():
    config = ConfigA(step_a=[StepConfigA("junk", "junka")], step_b=[StepConfigB("hello", 3.1)])

    with pytest.raises(AttributeError):
        get_config_for_step_id(config, step="junk", step_config_id="hello")


@pytest.mark.parametrize(
    "inp, exp, prefix",
    (
        pytest.param(23.4, 23.4, Path("/some/prefix"), id="no_change"),
        pytest.param(Path("hi"), Path("/some/prefix/hi"), Path("/some/prefix"), id="simple_path"),
        pytest.param(
            StepConfigC(
                step_config_id="step_id",
                helper=32.3,
                output=Path("location") / "to" / "somewhere.txt",
                config={"a": "b"},
            ),
            StepConfigC(
                step_config_id="step_id",
                helper=32.3,
                output=Path("/some") / "prefix" / "location" / "to" / "somewhere.txt",
                config={"a": "b"},
            ),
            Path("/some/prefix"),
            id="attribute_in_attrs_object",
        ),
        pytest.param(
            ConfigB(
                [
                    StepConfigC(
                        step_config_id="step_id",
                        helper=32.3,
                        output=Path("location") / "to" / "somewhere.txt",
                        config={"a": "b"},
                    ),
                    StepConfigC(
                        step_config_id="second",
                        helper=32.9,
                        output=Path("location") / "somewhere" / "else.txt",
                        config={"a": "b"},
                    ),
                ]
            ),
            ConfigB(
                [
                    StepConfigC(
                        step_config_id="step_id",
                        helper=32.3,
                        output=Path("/some/prefix") / Path("location") / "to" / "somewhere.txt",
                        config={"a": "b"},
                    ),
                    StepConfigC(
                        step_config_id="second",
                        helper=32.9,
                        output=Path("/some/prefix") / Path("location") / "somewhere" / "else.txt",
                        config={"a": "b"},
                    ),
                ]
            ),
            Path("/some/prefix"),
            id="nested_attrs_object",
        ),
    ),
)
def test_update_attr_value(inp, exp, prefix):
    res = update_attr_value(inp, prefix=prefix)

    assert res == exp


def test_load_hydrate_write_config_bundle(tmp_path):
    # Techincally not a unit test because it relies on our default converter_yaml...

    configuration_file = tmp_path / "source" / "configuration_file.yaml"
    configuration_file.parent.mkdir(parents=True)

    root_dir_output_run = tmp_path / "output-bundle" / "here"
    root_dir_output_run.mkdir(parents=True)

    run_id = "test_load_hydrate_write_config_bundle"

    load_config = partial(load_config_from_file, target=ConfigB, converter=converter_yaml)

    def create_cb(
        config_hydrated: ConfigB,
        config_hydrated_path: Path,
        root_dir_output_run: Path,
    ) -> ConfigBundleA:
        return ConfigBundleA(
            config_hydrated=config_hydrated,
            config_hydrated_path=config_hydrated_path,
            root_dir_output_run=root_dir_output_run,
            run_id=run_id,
        )

    config = ConfigB(
        step_c=[
            StepConfigC(
                step_config_id="only",
                helper=3.2,
                output=Path("to") / "somewhere.txt",
                config={"something": "here"},
            )
        ]
    )

    with open(configuration_file, "w") as fh:
        fh.write(converter_yaml.dumps(config))

    res = load_hydrate_write_config_bundle(
        configuration_file=configuration_file,
        load_configuration_file=load_config,
        create_config_bundle=create_cb,
        root_dir_output_run=root_dir_output_run,
        converter=converter_yaml,
    )

    assert isinstance(res, ConfigBundleA)
    assert isinstance(res.config_hydrated, ConfigB)
    assert res.config_hydrated_path == root_dir_output_run / configuration_file.name
    assert res.root_dir_output_run == root_dir_output_run
    assert res.run_id == run_id

    assert all(c.output.is_absolute() for c in res.config_hydrated.step_c)
    assert all(c.output.relative_to(root_dir_output_run) for c in res.config_hydrated.step_c)

    with open(res.config_hydrated_path) as fh:
        config_written = converter_yaml.loads(fh.read(), ConfigB)

    assert res.config_hydrated == config_written

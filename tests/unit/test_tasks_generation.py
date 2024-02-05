"""
Test tasks_generation module

Technically not a unit test, maybe should be moved to integration.
"""
import copy
import inspect
from collections.abc import Iterable
from pathlib import Path

from attrs import define

from pydoit_nb.config_handling import get_config_for_step_id
from pydoit_nb.notebook import ConfiguredNotebook, UnconfiguredNotebook
from pydoit_nb.notebook_step import UnconfiguredNotebookBasedStep
from pydoit_nb.serialization import converter_yaml
from pydoit_nb.tasks_generation import generate_all_tasks


@define
class ConfigOne:
    step_config_id: str
    factor: float


@define
class ConfigTwo:
    step_config_id: str
    name: str


@define
class Config:
    one: list[ConfigOne]
    two: list[ConfigTwo]


@define
class ConfigBundle:
    config_hydrated: Config
    run_id: str
    root_dir_output_run: Path
    config_hydrated_path: Path


@define
class StepDefiningModule:
    """Could also be a module, but class is clean here"""

    step: UnconfiguredNotebookBasedStep


def gen_zenodo_bundle_task(all_previous_tasks):
    return {
        "basename": "Zenodo bundle",
        "name": "Zenodo bundle generation",
        "docs": (
            "Left to to implementer to connect with other pydoit_nb functions. "
            "Here we just check it exists and that it received the other tasks "
            "as predecessors."
        ),
        "previous_tasks": all_previous_tasks,
    }


def configure_step_one(
    unconfigured_notebooks: Iterable[UnconfiguredNotebook],
    config_bundle: ConfigBundle,
    step_name: str,
    step_config_id: str,
):
    config = config_bundle.config_hydrated

    config_step = get_config_for_step_id(config=config, step=step_name, step_config_id=step_config_id)

    return [
        ConfiguredNotebook(
            unconfigured_notebook=unconfigured_notebooks[0],
            configuration=(config_step.step_config_id,),
            dependencies=(),
            targets=(),
            config_file=config_bundle.config_hydrated_path,
            step_config_id=step_config_id,
        )
    ]


def configure_step_two(
    unconfigured_notebooks: Iterable[UnconfiguredNotebook],
    config_bundle: ConfigBundle,
    step_name: str,
    step_config_id: str,
):
    return [
        ConfiguredNotebook(
            unconfigured_notebook=unconfigured_notebooks[0],
            dependencies=(),
            targets=(),
            config_file=config_bundle.config_hydrated_path,
            step_config_id=step_config_id,
        )
    ]


def make_dumpable(inp):
    tmp = copy.deepcopy(inp)
    if isinstance(tmp, dict):
        for k, v in tmp.items():
            tmp[k] = make_dumpable(v)

        return tmp

    if isinstance(tmp, str):
        return tmp

    if isinstance(tmp, Iterable):
        return type(tmp)(make_dumpable(v) for v in tmp)

    if callable(tmp):
        callable_str = str(tmp).split("at")[0]
        return callable_str

    # Block can be useful for debuggin
    # if tmp is not None and not isinstance(tmp, (str, float, Path, bool)):
    #     import pdb
    #
    #     pdb.set_trace()

    return tmp


def test_generate_all_tasks(file_regression):
    config_bundle = ConfigBundle(
        config_hydrated=Config(one=[ConfigOne("only", 3.3)], two=[ConfigTwo("solo", "hi")]),
        run_id="test_generate_all_tasks",
        root_dir_output_run=Path("/to") / "output" / "directory" / "root",
        config_hydrated_path=Path("/to") / "output" / "directory" / "root" / "config-hydrated.yaml",
    )
    root_dir_raw_notebooks = Path("/to") / "somewhere"
    converter = converter_yaml
    step_defining_modules = [
        StepDefiningModule(
            UnconfiguredNotebookBasedStep(
                step_name="one",
                unconfigured_notebooks=[
                    UnconfiguredNotebook(
                        notebook_path=Path("0xx_first") / "001_first",
                        raw_notebook_ext=".py",
                        summary="First notebook",
                        doc="Docs here",
                    )
                ],
                configure_notebooks=configure_step_one,
            )
        ),
        StepDefiningModule(
            UnconfiguredNotebookBasedStep(
                step_name="two",
                unconfigured_notebooks=[
                    UnconfiguredNotebook(
                        notebook_path=Path("1xx_second") / "111_step",
                        raw_notebook_ext=".py",
                        summary="Second notebook",
                        doc="Docs here for two",
                    )
                ],
                configure_notebooks=configure_step_one,
            )
        ),
    ]

    res = generate_all_tasks(
        config_bundle=config_bundle,
        root_dir_raw_notebooks=root_dir_raw_notebooks,
        converter=converter,
        step_defining_modules=step_defining_modules,
        gen_zenodo_bundle_task=gen_zenodo_bundle_task,
    )
    assert inspect.isgenerator(res)

    # Force generator to empty
    res = tuple(res)

    # Specific checks can go in here as we think of them

    # Use regression test too
    res_dumpable = []
    for v in res:
        res_dumpable.append(make_dumpable(v))

    res_dumpable = tuple(res_dumpable)
    file_regression.check(converter_yaml.dumps(res_dumpable))

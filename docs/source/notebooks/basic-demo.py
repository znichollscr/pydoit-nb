# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Basic demo
#
# This notebook gives a basic demonstration of how to use pydoit-nb.

# %% [markdown]
# ## Imports

# %%
from collections.abc import Iterable
from pathlib import Path

from attrs import field, frozen

import pydoit_nb
import pydoit_nb.serialization
from pydoit_nb.attrs_helpers import make_attrs_validator_compatible_single_input
from pydoit_nb.config_handling import get_config_for_step_id
from pydoit_nb.config_helpers import assert_step_config_ids_are_unique
from pydoit_nb.notebook import ConfiguredNotebook, UnconfiguredNotebook
from pydoit_nb.notebook_step import UnconfiguredNotebookBasedStep

# %%
print(f"You are using pydoit_nb version {pydoit_nb.__version__}")

# %% [markdown]
# ## Notebooks

# %% [markdown]
# ### Unconfigured
#
# The basic object is an `UnconfiguredNotebook`. This stores raw information about the notebook.

# %%
unconfigured = UnconfiguredNotebook(
    notebook_path=Path("/to") / "somewhere",
    raw_notebook_ext=".py",
    summary="Great notebook that does something",
    doc="More details can go here",
)
unconfigured

# %% [markdown]
# ### Configured
#
# To actually run the notebook, we have to configure it.
# You can just hard-code such configuration like the below.

# %%
configured = ConfiguredNotebook(
    unconfigured_notebook=unconfigured,
    dependencies=(Path("/to") / "some" / "file.txt",),
    targets=(Path("/to") / "some" / "file" / "the" / "notebook" / "creates.csv",),
    step_config_id="id-that-defines-which-step-in-the-workflow-this-notebook-belongs-to",
    config_file=Path("/to") / "config" / "file" / "to" / "pass" / "into" / "the" / "notebook.yaml",
    # For more on parameterising notebooks,
    # see papermill's documentation: https://papermill.readthedocs.io/en/latest/index.html
)
configured


# %% [markdown]
# However, normally this configuration of dependencies, targetes etc.
# is done at runtime because many details can only be completed at runtime
# (e.g. where we actually want to write the outputs
# usually depends on the exact environment we're running in).
# As a result, we tend to use `UnconfiguredNotebookBasedStep` instead.

# %% [markdown]
# ## Defining a notebook-based step
#
# To make the flow from `UnconfiguredNotebook` to `ConfiguredNotebook` a bit clearer and more flexible,
# we generally use `UnconfiguredNotebookBasedStep` objects as part of our workflow.
# These allow us to define sets of notebooks which make up different steps and to configure them at run time.
#
# The example below shows how you can go from a `UnconfiguredNotebook`
# and a configuration function and get out a task specification
# which can be understood by [pydoit](https://pydoit.org/contents.html).

# %% [markdown]
# The first step in this process is defining your configuration.
# At its simplest, you need to be able to create a configuration object
# and a configuration bundle which looks like the below (for more information,
# see `pydoit_nb.typing.ConfigBundleLike`).
# This is then used for configuring notebooks
# and keeping the configuration for a run all in one place.
# As you can see, it is extremely flexible and project specific
# which is why we don't provide generalised tooling for it.


# %%
@frozen  # using frozen makes the class hashable, which is handy
class PlotConfig:
    """
    Each step will have its own configuration

    For example, this would define the configuration for
    the plotting step.
    """

    step_config_id: str
    """
    An ID which defines this configuration for the step, unique within the workflow
    """

    colourscheme: str
    """
    Colourscheme

    This is just an example of how configuration can be stored
    """


@frozen
class Config:
    """
    Configuration

    This is passed to all the notebooks. It can contain
    whatever you want.
    """

    plot: list[PlotConfig] = field(
        validator=[
            # This validator can help you avoid confusing clashes
            # which are hard to debug later
            make_attrs_validator_compatible_single_input(assert_step_config_ids_are_unique)
        ]
    )
    """Configurations to use with the plotting step"""


@frozen
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

    root_dir_output_run: Path
    """Root output directory for this run"""


# %% [markdown]
# The next step is to define your function that will configure the notebooks.
# Defining it this way gives you full flexibility to do
# whatever you want to config the notebooks as you want them.


# %%
def configure_notebooks(
    unconfigured_notebooks: Iterable[UnconfiguredNotebook],
    config_bundle: ConfigBundle,
    step_name: str,
    step_config_id: str,
) -> list[ConfiguredNotebook]:
    """
    Configure the notebooks based on runtime information

    Parameters
    ----------
    unconfigured_notebooks
        Unconfigured notebooks

    config_bundle
        Configuration bundle from which to take configuration values

    step_name
        Name of the step

    step_config_id
        Step config ID to use when configuring the notebook

    Returns
    -------
        Configured notebooks
    """
    uc_nbs_dict = {nb.notebook_path: nb for nb in unconfigured_notebooks}

    config = config_bundle.config_hydrated

    config_step = get_config_for_step_id(config=config, step=step_name, step_config_id=step_config_id)

    configured_notebooks = [
        ConfiguredNotebook(
            unconfigured_notebook=uc_nbs_dict[Path("/to") / "somewhere"],
            # Dependencies and targets can come from config, other functions,
            # whatever.
            dependencies=(),
            targets=(),
            configuration=(config_step.colourscheme,),
            config_file=config_bundle.config_hydrated_path,
            step_config_id=step_config_id,
        ),
    ]

    return configured_notebooks


# %% [markdown]
# The last step is to put it altogether in a `UnconfiguredNotebookBasedStep`.

# %%
unconfigured_step = UnconfiguredNotebookBasedStep(
    step_name="plot",
    unconfigured_notebooks=[unconfigured],
    configure_notebooks=configure_notebooks,
)

# %% [markdown]
# This unconfigured step is now ready to be configured at run time.
#
# An example of this is below.

# %%
config_hydrated = Config(plot=[PlotConfig(step_config_id="blue", colourscheme="tab:blue")])
# This is normally hydrated based on run-time variables.
# Providing a complete working project is in our to-do list.
# In the meantime, see `tests/test-data/example-project`.

config_bundle = ConfigBundle(
    config_hydrated=config_hydrated,
    run_id="notebook_example",
    root_dir_output_run=Path("/to") / "output" / "directory",
    config_hydrated_path=Path("/to")
    / "output"
    / "directory"
    / "location-in-which-to-write-config-for-the-run.yaml",
)

# %%
notebook_tasks_generator = unconfigured_step.gen_notebook_tasks(
    config_bundle=config_bundle,
    root_dir_raw_notebooks=Path("notebooks"),
    converter=pydoit_nb.serialization.converter_yaml,
    # a pre-configured option, you can obviously make your own too
)
notebook_tasks_generator

# %% [markdown]
# The result is a generator, so we have to empty it to see what it actually does.

# %%
for task in notebook_tasks_generator:
    print(f"Task base name: {task['basename']}")
    print(f"Task name: {task['name']}")
    print(task)
    print()

# %% [markdown]
# The return value is a list of tasks which can be passed straight to [pydoit](https://pydoit.org/contents.html).

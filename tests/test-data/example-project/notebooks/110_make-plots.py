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
# # Plot
#
# Plot the data

# %% [markdown]
# ## Imports

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as nptype
from local.config import converter_yaml, load_config_from_file

from pydoit_nb.config_handling import get_config_for_step_id

# %% [markdown]
# ## Define the notebook-based step this notebook belongs to

# %%
step: str = "plot"

# %% [markdown]
# ## Parameters

# %% editable=true slideshow={"slide_type": ""} tags=["parameters"]
config_file: str = "dev-config-absolute.yaml"  # config file
step_config_id: str = "only"  # config ID to select for this branch

# %% [markdown]
# ## Load config

# %%
config = load_config_from_file(config_file)
config_step = get_config_for_step_id(config=config, step=step, step_config_id=step_config_id)

# %% [markdown]
# ## Action

# %% [markdown]
# ### Load draws


# %%
def load_file_to_np(fin: Path) -> nptype.NDArray[np.float64]:
    with open(fin) as fh:
        read = converter_yaml.loads(fh.read(), nptype.NDArray[np.float64])

    return read


loaded = {}
for md in config.make_draws:
    loaded[md.step_config_id] = {}
    loaded[md.step_config_id]["draws"] = load_file_to_np(md.file_draws)
    loaded[md.step_config_id]["scaled"] = load_file_to_np(md.file_draws_scaled)

# %% [markdown]
# ### Plot

# %%
for idx, axis in ((0, "x"), (1, "y")):
    for k, v in loaded.items():
        for sk in ["draws", "scaled"]:
            plt.hist(v[sk][:, idx], label=f"{k} {sk} {axis}", alpha=0.4)

    plt.legend()
    plt.show()

# %%
for k, v in loaded.items():
    for sk in ["draws", "scaled"]:
        plt.scatter(v[sk][:, 0], v[sk][:, 1], label=f"{k} {sk}", alpha=0.4, color=config_step.colour)

plt.legend()
config_step.file_plot.parent.mkdir(exist_ok=True, parents=True)
plt.savefig(config_step.file_plot)

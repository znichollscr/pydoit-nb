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
# # Set seed
#
# Set the seed for the workflow

# %% [markdown]
# ## Imports

# %%
from local.config import load_config_from_file

from pydoit_nb.config_handling import get_config_for_step_id

# %% [markdown]
# ## Define the notebook-based step this notebook belongs to

# %%
step: str = "set_seed"

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

# %%
config_step.file_seed.parent.mkdir(exist_ok=True, parents=True)
with open(config_step.file_seed, "w") as fh:
    fh.write(str(config_step.seed))

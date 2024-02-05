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
# # Scale draws
#
# Scale the draws

# %% [markdown]
# ## Imports

# %%
import numpy as np
import numpy.typing as nptype
from local.config import converter_yaml, load_config_from_file

from pydoit_nb.config_handling import get_config_for_step_id

# %% [markdown]
# ## Define the notebook-based step this notebook belongs to

# %%
step: str = "make_draws"

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
# ### Scale draws

# %%
with open(config_step.file_draws) as fh:
    draws = converter_yaml.loads(fh.read(), nptype.NDArray[np.float64])

# %%
scaled = draws * config_step.factor


# %%
with open(config_step.file_draws_scaled, "w") as fh:
    fh.write(converter_yaml.dumps(scaled))

config_step.file_draws_scaled

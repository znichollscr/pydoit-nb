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
# # Make draws
#
# Make draws of data

# %% [markdown]
# ## Imports

# %%
import numpy as np
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
config_set_seed = get_config_for_step_id(config=config, step="set_seed", step_config_id="only")

# %% [markdown]
# ## Action

# %%
N_DRAWS: int = 25

# %%
with open(config_set_seed.file_seed) as fh:
    seed = int(fh.read())

seed

# %% [markdown]
# ### Make draws

# %%
generator = np.random.Generator(np.random.PCG64(seed))

# %%
cov = np.array([[0.9, 0.1], [0.1, 0.3]])
draws = generator.multivariate_normal(
    mean=np.zeros_like(np.diag(cov)),
    cov=cov,
    size=N_DRAWS,
)

# %%
with open(config_step.file_draws, "w") as fh:
    fh.write(converter_yaml.dumps(draws))

config_step.file_draws

"""
[Doit](https://pydoit.org) configuration file for testing

TODO: discuss notes below

The key runtime config is currently handled with environment variables. Using
environment variables is great because it avoids the pain of doit's weird
command-line passing rules and order when doing e.g. `doit list`. However, it
does sort of break doit's database because doit's database is keyed based on
the task name, not the dependencies (using a json database makes this much much
easier to see which is why our dev runs use a json backend). To avoid this, I
currently make the database depend on the RUN_ID (see the mangling of
DOIT_CONFIG below). As a result, the database file changes as the run id
changes, so the database file is separate for each run id  and the issue of
different runs using the same database and hence clashing is avoided. This does
feel like a bit of a hack though, not sure if there is a better pattern or
whether this is actually best.

This ``dodo.py`` file can be configured using the following environment variables:

- ``EXAMPLE_PROJECT_RUN_ID``
    - The run ID to use with this run of the workflow

      Default: timestamp in YYYYMMDDHHMMSS format

- ``DOIT_DATABASE_BACKEND``
    - The kind of back-end to use for doit's database

      Default: "dbm"

- ``DOIT_DATABASE_FILE``
    - The file to use for doit's database

      Default: "doit_{EXAMPLE_PROJECT_RUN_ID}.db"

TODO: think about whether any of the below could be moved into pydoit-nb. It's
a bit hard to tell how much is general/re-usable and how much is not.
"""
from __future__ import annotations

import datetime as dt
import os
from collections.abc import Iterable
from functools import partial
from pathlib import Path

import local_make_draws
import local_plot
import local_retrieve_data

# Not great as package isn't installed, but fine for testing
import local_set_seed
from local_config import Config, ConfigBundle, converter_yaml, load_config_from_file

from pydoit_nb.config_handling import load_hydrate_write_config_bundle
from pydoit_nb.display import gen_show_configuration_task
from pydoit_nb.doit_tools import setup_logging
from pydoit_nb.tasks_copy_source import gen_copy_source_into_output_tasks
from pydoit_nb.tasks_generation import generate_all_tasks
from pydoit_nb.typing import DoitTaskSpec

RUN_ID: str = os.environ.get("EXAMPLE_PROJECT_RUN_ID", dt.datetime.now().strftime("%Y%m%d%H%M%S"))
"""ID to use with this run"""

DOIT_CONFIG: dict[str, str] = {
    "backend": os.environ.get("DOIT_DATABASE_BACKEND", "dbm"),
    "dep_file": os.environ.get("DOIT_DATABASE_FILE", f".doit_{RUN_ID}.db"),
}
"""
pydoit configuration

See https://pydoit.org/configuration.html#configuration-at-dodo-py
"""

logger = setup_logging()


def task_generate_workflow_tasks() -> Iterable[DoitTaskSpec]:
    """
    Generate workflow tasks

    This task pulls in the following environment variables:

    - ``EXAMPLE_PROJECT_CONFIGURATION_FILE``
        - The file to use to configure this run

          Default: "example-project-config.yaml"

    - ``EXAMPLE_PROJECT_ROOT_DIR_OUTPUT``
        - The directory to use as the root directory for outputs. If a relative
          path is supplied, this is converted to an absolute path.

          Default: "output-bundles"

    - ``EXAMPLE_PROJECT_ROOT_DIR_RAW_NOTEBOOKS``
        - The root directory in which the raw (i.e. not yet run) notebooks
          live. If a relative path is supplied, this is converted to an
          absolute path.

          Default: "notebooks"

    Yields
    ------
        Tasks which can be handled by :mod:`pydoit`
    """
    logger.info("Starting to generate doit tasks")

    configuration_file = Path(
        os.environ.get("EXAMPLE_PROJECT_CONFIGURATION_FILE", "example-project-config.yaml")
    ).absolute()

    # RUN_ID has to be retrieved in the global namespace so we can set
    # DOIT_CONFIG. I don't love this as we have two patterns, retrieve
    # environment variable into global variable and retrieve environment
    # variable within this function. However, I don't know which way is better
    # so haven't made a choice.
    run_id = RUN_ID

    root_dir_output = Path(os.environ.get("EXAMPLE_PROJECT_ROOT_DIR_OUTPUT", "output-bundles")).absolute()
    root_dir_raw_notebooks = Path(
        os.environ.get("EXAMPLE_PROJECT_ROOT_DIR_RAW_NOTEBOOKS", "notebooks")
    ).absolute()

    # TODO: consider giving the user more control over this or not
    root_dir_output_run = root_dir_output / run_id
    root_dir_output_run.mkdir(parents=True, exist_ok=True)

    # Data copying would go in here, if needed, lots of options in here for that

    yield gen_show_configuration_task(
        configuration_file=configuration_file,
        run_id=run_id,
        root_dir_output=root_dir_output,
        root_dir_raw_notebooks=root_dir_raw_notebooks,
    )

    # TODO: discuss
    # Current logic: put everything in a single configuration file.
    # The logic (however crazy) for generating that configuration file should
    # be kept separate from actually running all the notebooks to simplify
    # maintenance.
    def create_config_bundle(
        config_hydrated: Config,
        config_hydrated_path: Path,
        root_dir_output_run: Path,
    ) -> ConfigBundle:
        return ConfigBundle(
            config_hydrated=config_hydrated,
            config_hydrated_path=config_hydrated_path,
            root_dir_output_run=root_dir_output_run,
            run_id=run_id,
            root_dir_output=root_dir_output,
        )

    config_bundle = load_hydrate_write_config_bundle(
        configuration_file=configuration_file,
        load_configuration_file=load_config_from_file,
        create_config_bundle=create_config_bundle,
        root_dir_output_run=root_dir_output_run,
        converter=converter_yaml,
    )

    yield {
        "basename": "generate_workflow_tasks",
        "name": None,
        "doc": "Generate tasks for the workflow",
    }

    yield from generate_all_tasks(
        config_bundle=config_bundle,
        root_dir_raw_notebooks=root_dir_raw_notebooks,
        converter=converter_yaml,
        # Lots of control given through these bits
        step_defining_modules=[
            local_set_seed,
            local_make_draws,
            local_retrieve_data,
            local_plot,
        ],
        gen_zenodo_bundle_task=partial(
            gen_copy_source_into_output_tasks,
            repo_root_dir=Path(__file__).parent,
            root_dir_output_run=config_bundle.root_dir_output_run,
            run_id=config_bundle.run_id,
            root_dir_raw_notebooks=root_dir_raw_notebooks,
            config_file_raw=configuration_file,
            other_files_to_copy=(),
            src_dir="src",  # nothing in here for this example, but to illustrate the point
        ),
    )

    logger.info("Finished generating doit tasks")

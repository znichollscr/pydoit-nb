"""
Test the integration with pydoit
"""
from __future__ import annotations

import copy
import os
import subprocess
from pathlib import Path
from typing import TypeVar

import pytest

T = TypeVar("T")


@pytest.fixture(scope="session")
def example_project_dir() -> Path:
    return Path(__file__).parent.parent / "test-data" / "example-project"


def setup_doit_env_vars(test_name: str, env: T) -> T:
    env["EXAMPLE_PROJECT_RUN_ID"] = test_name
    env["DOIT_DATABASE_BACKEND"] = "json"
    env["DOIT_DATABASE_FILE"] = f"{test_name}.json"

    return env


def test_task_display(example_project_dir, tmp_path_factory, file_regression):
    env = setup_doit_env_vars("test-task-display", copy.deepcopy(os.environ))

    res = subprocess.run(
        ("doit", "list", "--all", "--status"),  # noqa: S603
        cwd=example_project_dir,
        env=env,  # may need virtual env setup here too
        stdout=subprocess.PIPE,
        check=False,
    )
    assert res.returncode == 0, res.stdout

    res_stdout = res.stdout.decode()

    # More specific tests can go here e.g. checking that certain lines look certain ways.
    # This may require actually parsing the stdout.

    # Use a regression test to help us keep track of what stdout produces
    file_regression.check(res_stdout)


# - test execute realises that task doesn't need to be re-run
# - test tasks can be run through

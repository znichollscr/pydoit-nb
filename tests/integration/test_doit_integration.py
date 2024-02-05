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

ROOT_DIR = Path(__file__).parent.parent.parent

T = TypeVar("T")


@pytest.fixture(scope="session")
def example_project_dir() -> Path:
    return Path(__file__).parent.parent / "test-data" / "example-project"


def setup_doit_env_vars(test_name: str, env: T) -> T:
    env["EXAMPLE_PROJECT_RUN_ID"] = test_name
    env["DOIT_DATABASE_BACKEND"] = "json"
    env["DOIT_DATABASE_FILE"] = f"{test_name}.json"

    return env


def assert_venv_dir_in_output(venv_dir_exp, output):
    assert str(venv_dir_exp / ".venv") in output, "venv set incorrectly"


def assert_tool_in_venv(tool, venv_dir, env):
    res_subprocess = subprocess.run(
        ("poetry", "run", "which", tool),  # noqa: S603
        cwd=venv_dir,
        env=env,
        stdout=subprocess.PIPE,
        check=False,
    )

    assert_venv_dir_in_output(venv_dir, res_subprocess.stdout.decode())


def assert_using_expected_venv(venv_dir_exp, env):
    res_venv = subprocess.run(
        ("poetry", "env", "info"),  # noqa: S603
        cwd=venv_dir_exp,
        env=env,
        stdout=subprocess.PIPE,
        check=True,
    )
    assert_venv_dir_in_output(venv_dir_exp, res_venv.stdout.decode())


def setup_venv(venv_dir, env, remove_lock_if_added: bool = True):
    try:
        del env["VIRTUAL_ENV"]
    except KeyError:
        pass

    lock_file = venv_dir / "poetry.lock"
    lock_exists = lock_file.exists()
    subprocess.run(("poetry", "config", "virtualenvs.in-project", "true"), cwd=venv_dir, env=env, check=True)  # noqa: S603
    subprocess.run(("poetry", "install", "--all-extras"), cwd=venv_dir, env=env, check=True)  # noqa: S603

    assert_tool_in_venv("pip", venv_dir, env)

    subprocess.run(
        ("poetry", "run", "pip", "install", "-e", str(ROOT_DIR)),  # noqa: S603
        cwd=venv_dir,
        env=env,
        stdout=subprocess.PIPE,
        check=False,
    )

    assert_using_expected_venv(venv_dir, env)

    if not lock_exists and remove_lock_if_added:
        # remove the lock file which was made by creating the virtual environment
        lock_file.unlink()

    return env


def test_task_display(example_project_dir, tmp_path_factory, file_regression):
    env = copy.deepcopy(os.environ)
    env = setup_venv(example_project_dir, env)
    env = setup_doit_env_vars("test-task-display", env)

    assert_tool_in_venv("doit", example_project_dir, env)

    res = subprocess.run(
        ("poetry", "run", "doit", "list", "--all", "--status"),  # noqa: S603
        cwd=example_project_dir,
        env=env,  # may need virtual env setup here too
        stdout=subprocess.PIPE,
        check=False,
    )
    assert res.returncode == 0, res.stdout.decode()

    res_stdout = res.stdout.decode()

    # More specific tests can go here e.g. checking that certain lines look certain ways.
    # This may require actually parsing the stdout.

    # Use a regression test to help us keep track of what stdout produces
    file_regression.check(res_stdout)


def test_task_run(example_project_dir, tmp_path_factory):
    # No regression test here at the moment. Maybe we'll at that in if it seems helpful.
    env = copy.deepcopy(os.environ)
    env = setup_venv(example_project_dir, env)
    env = setup_doit_env_vars("test-task-run", env)

    assert_tool_in_venv("doit", example_project_dir, env)

    res = subprocess.run(
        ("poetry", "run", "doit", "run", "--verbosity=2"),  # noqa: S603
        cwd=example_project_dir,
        env=env,  # may need virtual env setup here too
        stdout=subprocess.PIPE,
        check=False,
    )
    assert res.returncode == 0, res.stdout.decode()

    res_stdout = res.stdout.decode()

    # More specific tests can go here e.g. checking that certain lines look certain ways.
    # This may require actually parsing the stdout.
    assert f"run_id: {env['EXAMPLE_PROJECT_RUN_ID']}" in res_stdout

    # Other tests could go in here


# - test that execute realises that task doesn't need to be re-run
#   - run up to a given notebook step
#   - check the status
#   - ensure the status shows that the notebooks we've just been run don't need to be run again

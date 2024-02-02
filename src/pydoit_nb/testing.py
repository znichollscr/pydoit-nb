"""
Tools to help with testing
"""
from __future__ import annotations

import copy
from typing import Any


def assert_doit_tasks_equal(res: dict[str, Any], exp: dict[str, Any]) -> None:
    """
    Assert that doit tasks are equal

    This works around the fact that :class:`doit.tools.config_changed` objects
    don't compare equal in an easy to use way.

    Parameters
    ----------
    res
        Task to check

    exp
        Expected value of the task
    """
    # Copy the tasks before proceeding so that we can pop without affecting the
    # original result
    res_copy = copy.deepcopy(res)
    exp_copy = copy.deepcopy(exp)

    # doit doesn't implement a helpful comparison method so we have to do some
    # of our own comparison magic here
    res_uptodate = res_copy.pop("uptodate")
    assert len(res_uptodate) == 1

    exp_uptodate = exp_copy.pop("uptodate")
    assert len(exp_uptodate) == 1

    for attr in ("config", "config_digest", "encoder"):
        assert getattr(res_uptodate[0], attr) == getattr(exp_uptodate[0], attr)

    assert res_copy == exp_copy

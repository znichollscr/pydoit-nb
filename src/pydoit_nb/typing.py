"""
Typing specifications
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, TypeVar

from attrs import AttrsInstance

try:
    from typing_extensions import TypeAlias
except ImportError:  # >= python 3.11
    # remove type ignore when mypy applied with python 3.11
    from typing import TypeAlias  # type: ignore

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

DoitTaskSpec: TypeAlias = dict[str, Any]


class ConfigBundleLike(Protocol[T_co]):
    """
    Protocol for configuration bundles
    """

    @property
    def config_hydrated(self) -> T_co:
        """Hydrated config"""
        ...

    @property
    def config_hydrated_path(self) -> Path:
        """Path in which to write the hydrated config"""
        ...

    @property
    def root_dir_output_run(self) -> Path:
        """Root directory in which output is saved"""
        ...

    @property
    def run_id(self) -> str:
        """Run ID for the run to which this config bundle applies"""
        ...


AI_contra = TypeVar("AI_contra", bound=AttrsInstance, contravariant=True)
CB_co = TypeVar("CB_co", bound=ConfigBundleLike[Any], covariant=True)


class ConfigBundleCreator(Protocol[AI_contra, CB_co]):
    """
    Callable that can be used to create config bundles
    """

    def __call__(
        self, config_hydrated: AI_contra, config_hydrated_path: Path, root_dir_output_run: Path
    ) -> CB_co:
        """
        Create :obj:`ConfigBundleLike`

        Parameters
        ----------
        config_hydrated
            Hydrated config to include in the bundle

        config_hydrated_path
            Path where the hydrated config is saved to disk

        root_dir_output_run
            Root directory for the run's output

        Returns
        -------
            Created :obj:`ConfigBundleLike`
        """
        ...  # pragma: no cover


class Converter(Protocol):
    """
    Protocol for converters
    """

    def dumps(self, obj: Any, sort_keys: bool = False) -> str:
        """
        Dump configuration to a string

        Parameters
        ----------
        obj
            Object to dump. The type hints aren't great here. The assumption is
            that the dumping protocol should handle any type issues (I think
            static typing doesn't really work here, for reasons I don't fully
            have my head around).

        sort_keys
            Should the keys be sorted in the output?

        Returns
        -------
            String version of ``config``
        """
        ...  # pragma: no cover

    def loads(self, inp: str, target: type[T]) -> T:
        """
        Load an instance of ``target`` from a string

        Parameters
        ----------
        inp
            String to load from

        target
            Object type to return

        Returns
        -------
            Loaded instance of ``target``
        """
        ...  # pragma: no cover


class NotebookConfigLike(Protocol):
    """
    A class which is like a notebook config
    """

    step_config_id: str
    """String which identifies the step config to use with the notebook"""

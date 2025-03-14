"""Utilities for reading and writing files across data stores.
"""

# Standard library imports
import glob
import io
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Union

# Third-party imports
from django.conf import settings


class IDataStore(ABC):
    """Abstract class for accessing file systems."""

    @abstractmethod
    def list_contents(
        self,
        root_dir: Union[Path, str] = settings.DATA_DIR,
        glob_pattern: str = "**/**?",
    ) -> List[str]:
        """Recursively lists absolute paths to all files
        under the given root directory, with the option of
        filtering the paths using a glob pattern. Directories
        are ignored.

        References:
        - [glob — Unix style pathname pattern expansion](https://docs.python.org/3.11/library/glob.html)

        Args:
            root_dir (`pathlib.Path` | `str`): The absolute path to
                the parent/top-most directory of the file
                system. Defaults to the data directory
                defined in the Django settings module that
                corresponds to the current development environment.

            glob_pattern (`str`): A relative path to search
                for within the root directory. May contain
                shell-like wildcards. Defaults to `**/**?`, in
                which case all files under the root directory
                and its nested subdirectories are listed.

        Returns:
            (`list` of `str`): The list of absolute file paths
                matching the glob pattern within the directory.
        """
        raise NotImplementedError

    @abstractmethod
    @contextmanager
    def open_file(
        self,
        file_name: str,
        mode: str = "r",
        root_dir: Union[Path, str] = settings.DATA_DIR,
    ) -> Iterator[io.IOBase]:
        """Opens a file with the given name and mode.

        Args:
            file_name (`str`): The file name, representing the
                relative path to the file within the root directory.

            mode (`str`): The file opening method. Defaults to
                reading text ("r").

            root_dir (`pathlib.Path` | `str`): The designated
                parent/top-most directory of the file system.
                Defaults to the data directory defined in the
                constants module.

        Yields:
            (`io.IOBase`): A file object.
        """
        raise NotImplementedError


class LocalDataStore(IDataStore):
    """Concrete class for accessing local file systems."""

    def list_contents(
        self,
        root_dir: Union[Path, str] = settings.DATA_DIR,
        glob_pattern: str = "**/**?",
    ) -> List[str]:
        """Recursively lists relative paths to all files
        under the given root directory, with the option of
        filtering the paths using a glob pattern. Directories
        are ignored regardless of the pattern.

        References:
        - [glob — Unix style pathname pattern expansion](https://docs.python.org/3.11/library/glob.html)

        Args:
            root_dir (`pathlib.Path` | `str`): The absolute path to
                the parent/top-most directory of the file
                system. Defaults to the data directory
                defined in the Django settings module that
                corresponds to the current development environment.

            glob_pattern (`str`): A relative path to search
                for within the root directory. May contain
                shell-like wildcards. Defaults to `**/**?`, in
                which case all files under the root and any
                of its nested subdirectories are listed.

        Returns:
            (`list` of `str`): The list of relative file paths
                matching the glob pattern within the directory.
        """
        out = []
        for pth in glob.glob(glob_pattern, root_dir=root_dir, recursive=True):
            full_pth = Path(root_dir) / pth
            if os.path.isfile(full_pth):
                out.append(pth)
        return out

    @contextmanager
    def open_file(
        self,
        file_name: str,
        mode: str = "r",
        root_dir: Union[Path, str] = settings.DATA_DIR,
    ) -> Iterator[io.IOBase]:
        """Opens a file with the given name and mode.

        Args:
            file_name (`str`): The file name, representing the
                the relative path to the file within the root
                directory.

            mode (`str`): The file opening method. Defaults to
                reading text ("r").

            root_dir (`pathlib.Path` | `str`): The absolute path to
                the parent/top-most directory of the file
                system. Defaults to the data directory
                defined in the constants module.

        Yields:
            (`io.IOBase`): A file object.
        """
        # Resolve file path
        fpath = Path(root_dir) / file_name

        # Create file's parent directories if writing
        if not fpath.exists():
            Path(fpath).parent.mkdir(parents=True, exist_ok=True)

        # Detect UTF-8 BOM encoding if applicable
        try:
            with open(fpath, "rb") as f:
                first_bytes = f.read(3)
            encoding = "utf-8-sig" if first_bytes == b"\xef\xbb\xbf" else None
        except FileNotFoundError:
            encoding = None

        # Open file
        f = open(fpath, mode, encoding=encoding)

        # Yield file
        try:
            yield f
        finally:
            f.close()


class IDataStoreFactory:
    """Factory for fetching Singleton instance of a data store based on environment."""

    _helper: Optional[IDataStore] = None

    @staticmethod
    def get() -> IDataStore:
        """Fetches a local or cloud-based file system
        helper based on the current name of the
        development environment (e.g., "DEV" or "PROD").

        Args:
            `None`

        Returns:
            (`IDataStore`)
        """
        if not IDataStoreFactory._helper:
            env = os.environ.get("ENV", "DEV")
            if env == "DEV":
                IDataStoreFactory._helper = LocalDataStore()
            elif env == "PROD":
                pass
            else:
                raise RuntimeError(
                    "Unable to instantiate an `IDataStore`. Invalid "
                    f"environment variable passed for 'ENV': {env}."
                )
        return IDataStoreFactory._helper

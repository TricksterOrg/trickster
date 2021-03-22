"""Helper function for interaction with the underlying operating system."""

import os
import shutil
import glob

from typing import Iterator


def remove_file(file_path: str) -> None:
    """Remove file or directory including all its contents."""
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        shutil.rmtree(file_path)


def multi_glob(*patterns: str) -> Iterator[str]:
    """Perform glob search on all arguments."""
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            yield file_path

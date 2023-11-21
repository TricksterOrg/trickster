"""Module for accessing project metadata."""

import functools
import pathlib
import tomllib

from pydantic import BaseModel, FilePath

from trickster import TricksterError


project_root = pathlib.Path(__file__).parent.parent.absolute()


class MetadataError(TricksterError):
    """Exception used when something went wrong with the handling of the app's metadata."""


class Metadata(BaseModel):
    """Project metadata."""

    name: str
    description: str
    version: str
    authors: list[str]
    readme: FilePath


@functools.cache
def get_metadata() -> Metadata:
    """Get project metadata."""
    pyproject_file_path = project_root / 'pyproject.toml'
    try:
        with pyproject_file_path.open('rb') as pyproject_file:
            pyproject = tomllib.load(pyproject_file)
            raw_metadata = pyproject['tool']['poetry']
        raw_metadata['readme'] = str(project_root / raw_metadata['readme'])
        return Metadata.model_validate(raw_metadata)
    except (FileNotFoundError, IOError, KeyError) as e:
        raise MetadataError(f'Cannot load configuration file "{pyproject_file_path}".') from e


"""Initialization of CLI app."""

import os
import glob
import logging
import shutil

import click
from flask.cli import FlaskGroup

from trickster.api_app import ApiApp

from typing import List


TESTABLE_FILES = [
    'trickster',
    'app.py',
    'cli.py'
]

JUNK_FILES = [
    '*/*.pyc',
    '*/__pycache__',
    '.mypy_cache',
    '*.egg-info',
    '.pytest_cache',
    '.benchmarks',
    'htmlcov',
    '.coverage',
    'build',
    'dist'
]


logger = logging.getLogger()
app = ApiApp()


def execute(command: List[str]) -> None:
    """Execute shell command given as a list of arguments."""
    os.system(' '.join(command))


@click.group(cls=FlaskGroup)
def cli() -> None:
    """Management utility for the Trickster application."""


@cli.command()
@click.option('--tag', '-t', type=click.Choice(['integration', 'unit'], case_sensitive=False))
@click.option('--cov/--no-cov', default=True)
def test(tag: str = None, cov: bool = True) -> None:
    """Run all tests."""
    click.secho('Running tests', fg='yellow')
    command = ['py.test']
    if tag:
        command += [f' -m {tag}']
    if cov:
        for file in TESTABLE_FILES:
            command += ['--cov', file]
        for report in ['term', 'html']:
            command += ['--cov-report', report]
    execute(command)


@cli.command()
def style() -> None:
    """Check coding style."""
    click.secho('Running style checks', fg='yellow')
    execute(['flake8', *TESTABLE_FILES])


@cli.command()
def types() -> None:
    """Check typing."""
    click.secho('Running type checks', fg='yellow')
    execute(['mypy', *TESTABLE_FILES])


@cli.command()
@click.pass_context
def check(ctx: click.Context) -> None:
    """Run all checks."""
    for check in [test, style, types]:
        ctx.invoke(check)


@cli.command()
def clean() -> None:
    """Remove all temp file."""
    for pattern in JUNK_FILES:
        for file in glob.glob(pattern):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                else:
                    shutil.rmtree(file)
                click.secho(f'Deleted: {file}', fg='green')
            except Exception as error:
                click.secho(f'Failed to delete {file}: {str(error)}', fg='red')

"""Initialization of CLI app."""

import os
import glob
import logging
import shutil

import click
from flask.cli import FlaskGroup

from trickster.api_app import ApiApp


logger = logging.getLogger()
app = ApiApp()


@click.group(cls=FlaskGroup)
def cli() -> None:
    """Management utility for the Trickster application."""


@cli.command()
def tests() -> None:
    """Run all tests."""
    os.system('''
    py.test \
        --cov trickster \
        --cov app.py \
        --cov cli.py \
        --cov-report html \
        --cov-report term
    ''')


@cli.command()
def style() -> None:
    """Check coding style."""
    os.system('flake8 .')


@cli.command()
def types() -> None:
    """Check typing."""
    os.system('mypy trickster app.py cli.py')


@cli.command()
@click.pass_context
def check(ctx: click.Context) -> None:
    """Run all checks."""
    click.secho('Running tests', fg='yellow')
    ctx.invoke(tests)

    click.secho('Running style checks', fg='yellow')
    ctx.invoke(style)

    click.secho('Running type checks', fg='yellow')
    ctx.invoke(types)


@cli.command()
def clean() -> None:
    """Remove all temp file."""
    junk_files_patterns = [
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

    for pattern in junk_files_patterns:
        for file in glob.glob(pattern):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                else:
                    shutil.rmtree(file)
                click.secho(f'Deleted: {file}', fg='green')
            except Exception as error:
                click.secho(f'Failed to delete {file}: {str(error)}', fg='red')

"""Initialization of CLI app."""

import subprocess

import click

from trickster.api_app import ApiApp
from trickster.config import Config
from trickster.sys import multi_glob, remove_file


TESTABLE_FILES = [
    'trickster',
    'app.py',
    'cli.py'
]

JUNK_FILES = [
    # Cache
    '*/*.pyc',
    '*/__pycache__',
    # Build
    '*.egg-info',
    'build',
    'dist'
    # Mypy
    '.mypy_cache',
    # Pytest
    '.pytest_cache',
    '.benchmarks',
    # Coverage
    '.coverage',
    'htmlcov',
    'coverage.xml'
]


@click.group()
def cli() -> None:
    """CLI for Trickster."""


@cli.command()
@click.option('-p', '--port', default=Config.DEFAULT_PORT, help='The port to bind to.')
@click.option('-x', '--prefix', default=Config.DEFAULT_INTERNAL_PREFIX, help='Url prefix of internal endpoints.')
@click.option('-r', '--routes', type=click.Path(exists=True), help='Path to json file with default routes.')
def run(port: int, prefix: str, default_routes: str) -> None:
    """Start local Trickster app."""
    config = Config(internal_prefix=prefix, port=port, routes_path=default_routes)
    app = ApiApp(config)
    app.run()


@cli.command()
@click.option('--no-cov', is_flag=True, default=False)
@click.option('-t', '--tag', type=click.Choice(['integration', 'unit']))
def test(no_cov: bool, tag: str) -> None:
    """Run all tests."""
    click.secho('Running tests', fg='yellow')
    command = ['py.test']
    if tag:
        command += ['-m', tag]
    if not no_cov:
        for file in TESTABLE_FILES:
            command += ['--cov', file]
        for report in ['term', 'html', 'xml']:
            command += ['--cov-report', report]
    subprocess.run(command)


@cli.command()
def style() -> None:
    """Check coding style."""
    click.secho('Running style checks', fg='yellow')
    subprocess.run(['flake8', *TESTABLE_FILES])


@cli.command()
def types() -> None:
    """Check typing."""
    click.secho('Running type checks', fg='yellow')
    subprocess.run(['mypy', *TESTABLE_FILES])


@cli.command()
@click.pass_context
def check(ctx: click.Context) -> None:
    """Run all checks."""
    for check in [test, style, types]:
        ctx.invoke(check)


@cli.command()
def clean() -> None:
    """Remove all temp file."""
    for file_path in multi_glob(*JUNK_FILES):
        try:
            remove_file(file_path)
            click.secho(f'Deleted: {file_path}', fg='green')
        except Exception as error:
            click.secho(f'Failed to delete {file_path}: {str(error)}', fg='red')

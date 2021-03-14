"""Install Trickster and dependencies."""

import os

from setuptools import setup


def get_version() -> str:
    """Get current package version."""
    return os.environ.get('PACKAGE_VERSION', 'dev')


def main() -> None:
    """Build Trickster package."""
    setup(
        name='trickster',
        version=get_version(),
        python_requires='>=3.8',
        description='Trickester is a Python/Flask application for mocking REST APIs',
        long_description='',
        url='https://github.com/JakubTesarek/trickster',
        author='Jakub Tesarek',
        author_email='jakub@tesarek.me',
        license='unlicensed',
        include_package_data=True,
        packages=['trickster'],
        install_requires=[
            'flask',
            'fastjsonschema',
            'basicauth'
        ],
        extras_require={
            'dev': [
                'setuptools',
                'wheel',
                'flake8',
                'flake8-docstrings',
                'flake8-pytest',
                'flake8-eradicate',
                'flake8-print',
                'flake8-todo',
                'pytest',
                'pytest-repeat',
                'pytest-cov',
                'pytest-mock',
                'mypy',
                'twine'
            ]
        }
    )


if __name__ == '__main__':
    main()

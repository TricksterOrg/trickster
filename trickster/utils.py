"""Utility functions that don't fit anywhere else."""


def remove_none_values(values: dict) -> dict:
    """Remove None values from dict."""
    return {k: v for k, v in values.items() if v is not None}

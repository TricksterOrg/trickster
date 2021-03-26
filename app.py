"""Initialization of API app."""

from trickster.api_app import ApiApp
from trickster.config import Config


app = ApiApp(Config())

"""Configuration for gunicorn worker."""

from trickster.config import Config

bind = f'0.0.0.0:{Config.DEFAULT_PORT}'
workers = 4

timeout = 90
accesslog = '-'
errorlog = '-'
loglevel = 'info'

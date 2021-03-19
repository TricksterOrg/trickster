"""Configuration for gunicorn worker."""

bind = '0.0.0.0:5000'
workers = 4

timeout = 90
accesslog = '-'
errorlog = '-'
loglevel = 'info'

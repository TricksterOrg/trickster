# Trickster


## Run Trickster in Docker
There is prepared Docker image with Trickster [tesarekjakub/trickster](https://hub.docker.com/r/tesarekjakub/trickster), you can run it using:
```
docker pull tesarekjakub/trickster
docker run -p 8080:8080 tesarekjakub/trickster
```
You can run it at different port, e.g. to run it at port 12345 use `-p 12345:8080`.

## Run Trickster as Python package
You can also run Trickster as Python package, just download [trickster from PyPI](https://pypi.org/project/Trickster/) (ideally into some virtual environment) and `trickster` entrypoint will become available.
```
python -m pip install trickster
trickster
```

## Development
### Bootstrap
```
python3.11 -m venv venv  # create virtual environment
. venv/bin/activate  # activate virtal environment
python -m pip install poetry  # install poetry package manager
poetry install  # install dependencies
```
For local development there is prepared `docker-compose.yml` which simplifies running and building the Docker image locally.
You can use
```
docker-compose build
docker-compose up
```
to build image and run the Docker container locally.

We also use the [poethepoet](https://poethepoet.natn.io/) runner with shortcuts to above commands
```
poe build
poe run
```

### Tests and QA
You can run tests and QA checks (style, typing) using poe
```
poe check
```


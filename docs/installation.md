---
layout: default
nav_order: 1
---


# Installation

1. TOC
{:toc}

## Requirements
Trickster requires **Python >=3.8**.

## Install from Pypi
You may install Trickster as a [Pypi package](https://pypi.org/project/trickster):
`pip install trickster`

This will also create a command alias so you can start Trickster server by typing:
`trickster`

## Install from Github
Clone the [Trickster repository](https://github.com/JakubTesarek/trickster) and install the server:
```
git clone https://github.com/JakubTesarek/trickster
cd trickster
pip install -e ".[dev]"
```
To start the Trickster server, type:
`trickster`

Alternatively, if you are located inside the Trickster root directory, you may start the app using Flask:
`flask run`

## Install from Dockerhub
Trickster provides [docker image](https://hub.docker.com/repository/docker/tesarekjakub/trickster) you can install and run locally or on a server:
`docker pull tesarekjakub/trickster:latest`

To start the container, type:
`docker run -p 5000:5000 tesarekjakub/trickster`

https://hub.docker.com/repository/docker/tesarekjakub/trickster
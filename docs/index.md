---
layout: default
nav_exclude: true
---

[![tests](https://img.shields.io/github/workflow/status/JakubTesarek/trickster/Tests?style=flat-square)](https://github.com/JakubTesarek/trickster/actions/workflows/tests.yml) [![release](https://img.shields.io/github/v/release/JakubTesarek/trickster?style=flat-square)](https://github.com/JakubTesarek/trickster/releases) [![codecov](https://img.shields.io/codecov/c/github/JakubTesarek/trickster?style=flat-square)](https://codecov.io/gh/JakubTesarek/trickster)

# Trickster
{: .no_toc }

Trickster is a Python/Flask application providing configurable API. It allows you to configure requests and responses using REST API.

1. TOC
{:toc}

## Usecases
- **Local development.** Sometimes your app needs lots of other services to work properly. Setting all that infrastructure might me time consuming and sometimes not even possible. Mock Service allows you to mock all necessary upstream services.
- **Integration testing.** The same way you need to setup infrastructure to develop locally, it might equally difficult to setup integration environment. Some services are just too hard to configure so you can test all scenarios. By using Mock Service you define expected behaviour. If you later find a bug, it's easy to find if your assumptions about the infrastructure was wrong or if there's a bug somewhere else.
- **Performance testing.** When running performance tests, the upstream services might cause a bottleneck. The test then actually tests your infrastructure, not your application. Or you might want to test what your application will do when all the dependencies start responding slowly or raise errors.
- **Distributing work.** Distributing work on new project between teams is challenging when you don't have a working API. Mock Service allows you to specify and document the API beforehand so everyone can start developing as if they have everything they need.


## Quickstart
The fastest way to start using the [Hello World example](/trickster/cookbook/hello-world.html). It will quickly walk you throught checking that Trickster is installed properly. You will also create your first route and call it.
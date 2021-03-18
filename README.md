# Trickster
Trickster is a Python/Flask application providing configurable API. It allows you to configure requests and responses using REST API.

- [Project Homepage](https://github.com/JakubTesarek/trickster)
- [Documentation](https://jakubtesarek.github.io/trickster/)
- [Issues](https://github.com/JakubTesarek/trickster/issues)
- [PyPi](https://github.com/JakubTesarek/trickster/issues)
- [Dockerhub](https://github.com/JakubTesarek/trickster/issues)


## Usecases
- **Local development.** Sometimes your app needs lots of other services to work properly. Setting all that infrastructure might me time consuming and sometimes not even possible. Mock Service allows you to mock all necessary upstream services.
- **Integration testing.** The same way you need to setup infrastructure to develop locally, it might equally difficult to setup integration environment. Some services are just too hard to configure so you can test all scenarios. By using Mock Service you define expected behaviour. If you later find a bug, it's easy to find if your assumptions about the infrastructure was wrong or if there's a bug somewhere else.
- **Performance testing.** When running performance tests, the upstream services might cause a bottleneck. The test then actually tests your infrastructure, not your application. Or you might want to test what your application will do when all the dependencies start responding slowly or raise errors.
- **Distributing work.** Distributing work on new project between teams is challenging when you don't have a working API. Mock Service allows you to specify and document the API beforehand so everyone can start developing as if they have everything they need.


## Quickstart
Create new Route:

```sh
curl --location --request POST '/internal/routes' --header 'Content-Type: application/json' --data-raw '{
    "path": "/endpoint",
    "responses": [
        {
            "body": "response"
        }
    ]
}'
```
You configured a new Route that lives on `/endpoint`. When you call it, it will return HTTP 200 and string `response`.

You can test it by calling:

```sh
curl --location --request GET '/endpoint'
```

Of course, Trickster provides way more possibilities to configure how the Routes will work. All features are described in [documentation](https://jakubtesarek.github.io/trickster/).
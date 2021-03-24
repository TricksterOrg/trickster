---
title: Authentication
layout: default
nav_order: 4
parent: API
---

# Authentication
{: .no_toc }

This section provides close look at authentication in Trickster. After reading in, you should understand how to set up authentication for your Routes.

> Authentication in Tricster is under development. The authentication methods and configuration will probably change in the future. If you encounter and error or you are missing a feature, please [create an issue](https://github.com/JakubTesarek/trickster/issues).

We also prepared [a tutorial that focuses on authentication](/trickster/cookbook/login-form.html). It introduces authentication on an example of a login/logout form. If you are not not familiar with authentication at all, it might be a good place to start.

1. TOC
{:toc}


## Configuring authentication

You can attach authentication method to each of your Routes. If you do and a request is matched by a Route with authentication, Trickster will check if the request contains the correct values. If it does, it will return Response as normal. If not, it will return a [401 Unauthorized error](/trickster/api/responses.html#401-unauthorized).

By default Route doesn't authenticate requests.

To attach an authentication method to Route, use [`authentication` attribute of a Route](/trickster/api/model.html#authentication).

Authentication can be set for any Route, regardles of it's HTTP method. Some types of authentication like Basic work with all HTTP methods just fine. Others, like Form, can be set for but they don't work well with GET http method. You can still call the Route but since only matches GET requests and you can't sent form data, the authentication will never succeed.



## Authentication methods

Each authentication method is represented as a JSON object. Each has to have an attribute `method` that specifies the authentication method to use. It can have any number of other attributes. Theses attributes are described in section of each method.


### Token authentication

Example:

```json
{
    "method": "token",
    "token": "my_token"
}
```

This method checks that incomming request contains header `Authorization` with value of `Bearer my_token`.


### Basic authentication

Example:

```json
{
    "method": "basic",
    "username": "my_username",
    "password": "my_password"
}
```

This method checks that incomming request contains header `Authorization` with value of `Bearer base64(my_username:my_password)`.


### Form authentication

Example:

```json
{
    "method": "form",
    "fields": {
        "field1": "value1",
        "field2": "value2",
        // ...
    }
}
```

This methods reads the form fields from incomming request and checks if all the fields specified in `fields` are present and that they contain the required value.

User can send more form fields than specified. Only the specified fields are validated.

Form authentication is usefull if you want to mock a login form.


### Cookie authentication

Example:

```json
{
    "method": "cookie",
    "name": "my_cookie",
    "value": "cookie_value"
}
```

This authentication reads the user cookies and check if there is a cookie `name` with value `value`.


### HMAC authentication

Example:

```json
{
    "method": "hmac",
    "key": "secret_key"
}
```

> Note that this authentication method will probably be changed in near future.

Hmac authentication checks if the request URL is signed with `sha1 hmac` algorithm.

It requires two URL arguments: `hmac_timestamp` and `hmac_sign`.

`hmac_timestamp` should contain current unix timestamp.

`hmac_sign` should contain a hmac sign generated using the `hmac_timestamp` and the key specified in the authentication method.
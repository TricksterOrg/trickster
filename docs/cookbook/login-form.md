---
title: Login Form
layout: default
nav_order: 1
parent: Cookbook
---

# Login Form
{: .no_toc }

In this recipe we will setup Trickster to emulate a website that provides login functionality. We will create a login page and a page that requires user to be logged-in. We'll also add a logout link.

> If you want to know more about authentication in general, visit [api documentation](/trickster/api/authentication).


1. TOC
{:toc}

## Create login form

First, we'll create a page that will display a login form to the user. 

Do do that we'll add new Route that will return the html content of the form. This is just a simple html containing only the necessary code but it will work as demonstration. We also set the `content-type` header so the browser recognizes the payload as html.

We don't specify http method which means that Trickster will use `GET` as default:

```python
import requests

response = requests.post('http://localhost:8080/internal/routes', json={
    'path': '/login',
    'responses': [{
        'headers': {
            'content-type': 'text/html'
        },
        'body': '''
<form method="POST">
    <input type="text" name="username">
    <input type="password" name="password">
    <input type="submit" value="login">
</form>
        '''
    }]
})
```

After you run this code, you can open in [http://localhost:8080/login](http://localhost:8080/login) in browser and should see the login form.

You can try to submit it but you'll notice you get an error. That's because we didn't create a Route that would handle the form yet.


## Process the login form
In previous section we created a Route that displays login form. In this step, we'll process the login the form.

When user submits the form, there are 3 things, that should happen:

1. We should validate that the username and password are correct
2. Set a session cookie
3. Redirect the user to secured section of the web

Let's create new Route that does all 3 things.

```python
import requests

response = requests.post('http://localhost:8080/internal/routes', json={
    'path': '/login',
    'method': 'POST',
    'auth': {
        'method': 'form',
        'fields': {
            'username': 'admin',
            'password': 'password1'
        }
    },
    'responses': [{
        'status': 301,
        'headers': {
            'Set-Cookie': 'session=123456789'
            'Location': '/admin'
        },
        'body': ''
    }]
})
```

There are some things to notice here.

First, we created new Route that listens on the same url as the previous one. This is not a problem because this one listens for `POST` request, not `GET`.

Then we configured the `auth` section to validate the form and look for fields `username` and `password`. As you see, the username is `admin` and password is `password1`. These are not the safest credentials but this is just a demo.

If the user sends valid credentials, the Route will return a Response with http status `301 Moved Permanently`. This instructs the browser to look for a `Location` header. And as you can see, we added this header as well. It means user will get redirected to our secure page `/admin`.

The last thing we did was adding a session cookie with value `123456789`. In next step, we'll create a Route handling the `/admin` page that will look for that cookie.


> You might have notice we didn't create a special response for users that don't send valid credentials. Unfortunately Trickster doesn't support this yet. Please see [Issue #8](https://github.com/JakubTesarek/trickster/issues/8) for more details.

> We also had to send a field `body` even though we set it to empty string. There is an [Issue #10](https://github.com/JakubTesarek/trickster/issues/10) that will solve this.


## Create secure page
In previous steps we create two Routes that handle login form. Now we'll create a page that we be awailable only to authenticated users.

```python
import requests

response = requests.post('http://localhost:8080/internal/routes', json={
    'path': '/admin',
    'auth': {
        'method': 'cookie'
        'name': 'session',
        'value': '123456789'
    }
    'responses': [{
        'headers': {
            'content-type': 'text/html'
        },
        'body': '''
<h1>Admin section<h1>
<p>Hello admin!</p>
<p><a href="/logout">logout</a></p>
        '''
    }]
})
```

Here we used a different authentication method. The `cookie` method looks for a cookie and checks if it has the correct value. In this case we look for the session we set in previous Route.

You can now test the login in your browser. Open [http://localhost:8080/login](http://localhost:8080/login), fill in the credentials and click on `login`. You should be redirected to the secure [admin page](http://localhost:8080/login).


## Enable logout
To finish this login workflow, we'll add handler that will log the user out. At this point it should be fairly obvious that we'll simply add another Route:

```python
import requests

response = requests.post('http://localhost:8080/internal/routes', json={
    'path': '/logout',
    'responses': [{
        'status': 301,
        'headers': {
            'Set-Cookie': 'session=deleted; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
            'Location': '/login'
        },
        'body': ''
    }]
})
```

This last Route is the simplest from all that we created today. It deletes the `session` cookie so the user is no longer authenticated and then redirects him back to [login page](http://localhost:8080/login).

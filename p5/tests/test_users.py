from flask import session, request
import pytest

from types import SimpleNamespace

from flask_app.forms import RegistrationForm, UpdateUsernameForm
from flask_app.models import User


def test_register(client, auth):
    """ Test that registration page opens up """
    resp = client.get("/register")
    assert resp.status_code == 200

    response = auth.register()
    assert response.status_code == 200
    user = User.objects(username="test").first()

    assert user is not None


@pytest.mark.parametrize(
    ("username", "email", "password", "confirm", "message"),
    (
        ("test", "test@email.com", "test", "test", b"Username is taken"),
        ("p" * 41, "test@email.com", "test", "test", b"Field must be between 1 and 40"),
        ("username", "test", "test", "test", b"Invalid email address."),
        ("username", "test@email.com", "test", "test2", b"Field must be equal to"),
    ),
)
def test_register_validate_input(auth, username, email, password, confirm, message):
    if message == b"Username is taken":
        auth.register()

    response = auth.register(username, email, password, confirm)

    assert message in response.data


def test_login(client, auth):
    """ Test that login page opens up """
    resp = client.get("/login")
    assert resp.status_code == 200

    auth.register()
    response = auth.login()

    with client:
        client.get("/")
        assert session["_user_id"] == "test"


@pytest.mark.parametrize(
     ("username",   "password",  "message"), 
    (("",           "test",     b"This field is required"),
     ("test",       "",         b"This field is required"),
     ("xxx",        "test",     b"Login failed. Check your username and/or password"),
     ("test",       "xxx",      b"Login failed. Check your username and/or password")))
def test_login_input_validation(auth, username, password, message):
    """
    Test that if you try to log in with an empty (1) username or (2) password, you get the error "This field is required"
    Test that when you successfully register but have (1) a bad username or (2) a bad password, you get the error message "Login failed. Check your username and/or password"
    """
    response = auth.login(username=username, password=password)
    assert response.status_code == 200
    assert message in response.data


def test_logout(client, auth):
    """
    Register, login, check that you successfully logged in, and then logout, and check that you successfully logged out
    """
    # Register, login
    username = "test"
    auth.register(username=username)
    response = auth.login(username=username)
    assert response.status_code == 200

    with client:
        client.get("/")
        assert session["_user_id"] == username

    # Logout
    response = auth.logout()
    assert response.status_code == 302 # Redirects

    # Assert that we have no session ID
    with pytest.raises(KeyError):
        with client:
            client.get("/")
            session["_user_id"]



def test_change_username(client, auth):
    username = "test"
    new_username = "test2"
    auth.register(username=username)
    auth.login(username=username)

    # Test that the account page loads successfully...
    response = client.get("/account")
    print(response.data)
    assert response.status_code == 200
    
    # ...and that you can successfully change the username of the logged-in user.
    update_username = SimpleNamespace(
        username=new_username,
        submit="Submit",
    )
    form = UpdateUsernameForm(formdata=None, obj=update_username)
    response = client.post("/account", data=form.data, follow_redirects=True)
    assert response.status_code == 200

    """
    with client:
        client.get("/")
        print(session)
        assert session["_user_id"] == new_username
    """

    auth.login(username=new_username)
    with client:
        # Test that the new username shows up on the account page
        response = client.get("/account")
        #assert response.status_code == 200
        print(response.data)
        assert new_username.encode('utf-8') in response.data

        # Test that the new username change is reflected in the database
        user = User.objects(username=new_username).first()
        assert user
        # Test that the old username isn't in the database 
        user = User.objects(username=username).first()
        assert not user


def test_change_username_taken(client, auth):
    # Test that if we try to change the username to a different user's username, then we get the error message "That username is already taken"

    username_1 = "test"
    username_2 = "test2"
    message = b"That username is already taken"

    # Add first user
    auth.register(username=username_1)
    auth.logout()

    # Add second user
    auth.register(username=username_2, email="test2@test.com")
    response = auth.login(username=username_2)
    assert response.status_code == 200

    update_username = SimpleNamespace(
        username=username_1,
        submit="Submit",
    )
    form = UpdateUsernameForm(formdata=None, obj=update_username)
    response = client.post("/account", data=form.data, follow_redirects=True)
    assert response.status_code == 200
    print(response.data)
    assert message in response.data

@pytest.mark.parametrize(
     ("new_username",  "message"), 
    (("",             b"This field is required"),
     ("t"*41,         b"Field must be between 1 and 40 characters long.")
    )
)
def test_change_username_input_validation(client, auth, new_username, message):
    """
    Test that if we pass in an empty string, we get the error "This field is required."
    Test that if we pass in a string that's too long, we get the error "Field must be between 1 and 40 characters long.
    """
    auth.register()
    auth.login()

    update_username = SimpleNamespace(
        username=new_username,
        submit="Submit",
    )
    form = UpdateUsernameForm(formdata=None, obj=update_username)
    response = client.post("/account", data=form.data, follow_redirects=True)
    print(response.data)
    assert message in response.data


import pytest

from types import SimpleNamespace
import random
import string

from flask_app.forms import SearchForm, MovieReviewForm
from flask_app.models import User, Review

def generate_random_string(length=100):
    return bytes(''.join(
        random.choices(
            string.ascii_uppercase + string.digits, 
            k=length)), 'utf-8')

def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200

    search = SimpleNamespace(search_query="guardians", submit="Search")
    form = SearchForm(formdata=None, obj=search)
    response = client.post("/", data=form.data, follow_redirects=True)

    assert b"Guardians of the Galaxy" in response.data


@pytest.mark.parametrize(
     ("query",            "message"), 
    (("",                b"This field is required."),
     ("a",               b"Too many results"),
     ("qqqqqqqqqqqqqqq", b"Movie not found"),
     ("x"*101,           b"Field must be between 1 and 100 characters long")
    )
)
def test_search_input_validation(client, query, message):
    search = SimpleNamespace(search_query=query, submit="Search")
    form = SearchForm(formdata=None, obj=search)
    response = client.post("/", data=form.data, follow_redirects=True)
    assert response.status_code == 200
    assert message in response.data


def test_movie_review(client, auth):
    # A beginning implementation is already provided to check if the movie detail page for the 'Guardians of the Galaxy' page will show up. The choice of this id is arbitrary, and you can change it to something else if you want.
    guardians_id = "tt2015381"
    url = f"/movies/{guardians_id}"
    
    resp = client.get(url)
    assert resp.status_code == 200

    # Register and login
    username = "tester"
    auth.register(username=username)
    auth.login(username=username)
    
    # Submit a movie review with a randomly generated string (to make sure that you're adding a truly unique review)
    review_content = generate_random_string(100)
    review = SimpleNamespace(
        text=review_content,
        submit="Submit"
    )
    form = MovieReviewForm(formdata=None, obj=review)
    resp = client.post(url, data=form.data, follow_redirects=True)
    assert resp.status_code == 200

    # Test that the review shows up on the page
    resp = client.get(url)
    assert review_content in resp.data

    # Test that the review is saved in the database
    user = User.objects(username=username).first()
    review = Review.objects(
        commenter=user,  
        content=review_content.decode('utf-8')
    ).first()
    assert review


@pytest.mark.parametrize(
     ("movie_id",   "error_code",   "message"), 
    (("",           404,            b"404 - Page Not Found"),
     ("12345678",   302,            b"Incorrect IMDb ID"),
     ("123456789",  302,            b"Incorrect IMDb ID"),
     ("1234567890", 302,            b"Incorrect IMDb ID")
    )
)
def test_movie_review_redirects(client, movie_id, error_code, message):
    """
    Test that with an empty movie_id, you get a status code of `404` and that you see the custom 404 page.
    Test that with (1) a movie_id shorter than 9 characters, (2) a movie_id exactly 9 characters (but an invalid id), and (3) a movie_id longer than 9 characters, the request has a status code of `302` and the error message "Incorrect IMDb ID" is displayed on the page you're redirected to."""
    url = f"/movies/{movie_id}"
    resp = client.get(url)
    assert resp.status_code == error_code
    
    resp = client.get(url, follow_redirects=True)
    assert message in resp.data


@pytest.mark.parametrize(
     ("comment",    "message"), 
    (("",          b"This field is required"),
     ("a"*4,       b"Field must be between 5 and 500 characters long."),
     ("a"*501,     b"Field must be between 5 and 500 characters long."),
     )
)
def test_movie_review_input_validation(client, auth, comment, message):
    """
    This test checks whether the proper validation errors from `MovieReviewForm` are raised when you provide incorrect input.
    Test that with an empty string, you get the error "This field is required"
    Test that with (1) a string shorter than 5 characters and (2) a string longer than 500 characters, you get the error "Field must be between 5 and 500 characters long."
    You can use any movie id here, just make sure it's valid or your test will fail.
    """
    guardians_id = "tt2015381"
    url = f"/movies/{guardians_id}"
    
    # Register and login
    username = "tester"
    auth.register()
    auth.login()

    # Send review
    review = SimpleNamespace(
        text=comment,
        submit="Submit"
    )
    form = MovieReviewForm(formdata=None, obj=review)
    resp = client.post(url, data=form.data, follow_redirects=True)
    assert resp.status_code == 200
    assert message in resp.data

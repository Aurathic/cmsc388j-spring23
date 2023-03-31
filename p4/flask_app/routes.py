# 3rd-party packages
from flask import render_template, request, redirect, url_for, flash
from flask_mongoengine import MongoEngine
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
)

from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import pathlib

# stdlib
from datetime import datetime

# local
from . import app, bcrypt, client
from .forms import (
    SearchForm,
    MovieReviewForm,
    RegistrationForm,
    LoginForm,
    UpdateUsernameForm,
    UpdatePasswordForm,
    UpdateProfilePicForm,
)
from .models import User, Review, load_user
from .utils import current_time

""" ************ View functions ************ """


@app.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    carousel_movie_ids = ["tt0800369", "tt2015381", "tt0033467"]
    try:
        carousel_movies = [
            client.retrieve_movie_by_id(movie_id) for movie_id in carousel_movie_ids
        ]
    except Exception as e:
        flash(str(e))
        return render_template("index.html", form=form)

    if form.validate_on_submit():
        return redirect(url_for("query_results", query=form.search_query.data))

    return render_template("index.html", form=form, carousel_movies=carousel_movies)


@app.route("/search-results/<query>", methods=["GET"])
def query_results(query):
    try:
        results = client.search(query)
    except Exception as e:
        flash(str(e))
        return render_template("query.html")

    # Get the average rating for each movie
    ratings = get_average_ratings(results)
    return render_template("query.html", results=results, ratings=ratings)


@app.route("/movies/<movie_id>", methods=["GET", "POST"])
def movie_detail(movie_id):
    try:
        result = client.retrieve_movie_by_id(movie_id)
    except Exception as e:
        flash(str(e))
        return render_template("movie_detail.html")

    form = MovieReviewForm()
    if form.validate_on_submit():
        if form.rating and form.rating.data != "No rating":
            review = Review(
                commenter=current_user._get_current_object(),
                content=form.text.data,
                date=current_time(),
                imdb_id=movie_id,
                movie_title=result.title,
                rating=form.rating.data,
            )
        else:
            review = Review(
                commenter=current_user._get_current_object(),
                content=form.text.data,
                date=current_time(),
                imdb_id=movie_id,
                movie_title=result.title,
            )
        review.save()
        return redirect(request.path)

    reviews = Review.objects(imdb_id=movie_id)
    rating = get_average_rating(movie_id)
    print(rating)
    return render_template(
        "movie_detail.html", form=form, movie=result, reviews=reviews, rating=rating
    )


@app.route("/user/<username>")
def user_detail(username):
    user = User.objects(username=username).first()
    if user is None:
        flash(f'The user "{username}" does not exist.')
        return render_template("user_detail.html")
    else:
        reviews = Review.objects(commenter=user)
        return render_template("user_detail.html", user=user, reviews=reviews)


@app.errorhandler(404)
def custom_404(e):
    return render_template("404.html")


""" ************ User Management views ************ """


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        flash("You're already logged in.")
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        user.save()
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You're already logged in.")
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(username=form.username.data).first()
        login_user(user)
        return redirect(url_for("account"))

    return render_template("login.html", form=form)


@login_required
@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.")
    else:
        flash("You need to be logged in first.")
    return redirect(url_for("index"))


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    print("account")
    username_update_form = UpdateUsernameForm()
    password_update_form = UpdatePasswordForm()
    profile_pic_update_form = UpdateProfilePicForm()

    # If valid, save updated username
    if (
        username_update_form.submit_username.data
        and username_update_form.validate_on_submit()
    ):
        current_user.modify(username=username_update_form.username.data)
        current_user.save()
        flash("Your username has been updated successfully.", "success")

    # If valid, save updated username
    print(
        "submit",
        password_update_form.submit_password.data,
        "password",
        password_update_form.password.data,
        "confirm password",
        password_update_form.confirm_password.data,
    )
    if (
        password_update_form.submit_password.data
        and password_update_form.validate_on_submit()
    ):
        hashed_password = bcrypt.generate_password_hash(
            password_update_form.password.data
        ).decode("utf-8")
        print(":: password", password_update_form.password.data, "->", hashed_password)
        current_user.modify(password=hashed_password)
        current_user.save()
        flash("Your password has been updated successfully.", "success")

    # If valid, save updated profile picture
    print(profile_pic_update_form.submit_profile_pic.data)
    if (
        profile_pic_update_form.submit_profile_pic.data
        and profile_pic_update_form.validate_on_submit()
    ):
        img = profile_pic_update_form.profile_pic.data
        filename = secure_filename(img.filename)
        content_type = f"img/{pathlib.Path(filename).suffix}"

        # Add new picture if none exists, otherwise update
        if current_user.profile_pic.get() is None:
            current_user.profile_pic.put(img.stream, content_type=content_type)
        else:
            current_user.profile_pic.replace(img.stream, content_type=content_type)
        current_user.save()
        flash("Your profile picture has been updated successfully.", "success")

    return render_template(
        "account.html",
        username_update_form=username_update_form,
        password_update_form=password_update_form,
        profile_pic_update_form=profile_pic_update_form,
    )


""" Other functions... """


# NEW FUNCTION
def get_average_ratings(movies):
    movie_ids = [movie.imdb_id for movie in movies]
    # Aggregate the ratings for the given movie_ids
    pipeline = [
        {"$match": {"imdb_id": {"$in": movie_ids}, "rating": {"$exists": True}}},
        {"$group": {"_id": "$imdb_id", "avg_rating": {"$avg": "$rating"}}},
    ]
    result = list(Review.objects().aggregate(pipeline))
    avg_ratings = {}
    for doc in result:
        avg_ratings[doc["_id"]] = doc["avg_rating"]
    return avg_ratings


def get_average_rating(imdb_id):
    pipeline = [
        {"$match": {"imdb_id": imdb_id, "rating": {"$exists": True}}},
        {"$group": {"_id": "$imdb_id", "avg_rating": {"$avg": "$rating"}}},
    ]
    result = list(Review.objects().aggregate(pipeline))
    avg_ratings = {}
    for doc in result:
        avg_ratings[doc["_id"]] = doc["avg_rating"]
    return avg_ratings[imdb_id] if imdb_id in avg_ratings else None

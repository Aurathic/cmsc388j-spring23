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
    UpdateProfilePicForm,
)
from .models import User, Review, load_user
from .utils import current_time

""" ************ View functions ************ """


@app.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("query_results", query=form.search_query.data))

    return render_template("index.html", form=form)


@app.route("/search-results/<query>", methods=["GET"])
def query_results(query):
    try:
        results = client.search(query)
    except ValueError as e:
        return render_template("query.html", error_msg=str(e))

    return render_template("query.html", results=results)


@app.route("/movies/<movie_id>", methods=["GET", "POST"])
def movie_detail(movie_id):
    try:
        result = client.retrieve_movie_by_id(movie_id)
    except ValueError as e:
        return render_template("movie_detail.html", error_msg=str(e))

    form = MovieReviewForm()
    if form.validate_on_submit():
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

    return render_template(
        "movie_detail.html", form=form, movie=result, reviews=reviews
    )


@app.route("/user/<username>")
def user_detail(username):
    return "user_detail"


def custom_404():
    pass


""" ************ User Management views ************ """


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
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
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(username=form.username.data).first()
        login_user(user)
        return redirect(url_for("account"))

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    print("account")
    username_update_form = UpdateUsernameForm()
    profile_pic_update_form = UpdateProfilePicForm()

    # If valid, save updated username
    if (
        username_update_form.submit_username.data
        and username_update_form.validate_on_submit()
    ):
        current_user.modify(username=username_update_form.username.data)
        current_user.save()

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
        profile_pic_update_form=profile_pic_update_form,
    )

# 3rd-party packages
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Blueprint,
    session,
    g,
)
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

# stdlib
from datetime import datetime
import io
import base64

# local
from . import bcrypt, movie_client
from .forms import (
    SearchForm,
    MovieReviewForm,
    RegistrationForm,
    LoginForm,
    UpdateUsernameForm,
)
from .models import User, Review, load_user
from .utils import current_time


main = Blueprint("main", __name__)


""" ************ View functions ************ """


@main.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("main.query_results", query=form.search_query.data))

    return render_template("index.html", form=form)


@main.route("/user/<username>")
def user_detail(username):
    user = User.objects(username=username).first()
    reviews = Review.objects(commenter=user)

    return render_template("user_detail.html", username=username, reviews=reviews)

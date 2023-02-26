# 3rd-party packages
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo

# stdlib
import os
from datetime import datetime

# local
from flask_app.forms import SearchForm, MovieReviewForm
from flask_app.model import MovieClient

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/database"
app.config["SECRET_KEY"] = b"*\x87-\xa3\x02l\xc0\x02\xfe\xa2i\x8dS\x82y\xd4"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

mongo = PyMongo(app)

key = os.environ.get("OMDB_API_KEY")
print(key)
client = MovieClient(key)

# --- Do not modify this function ---
@app.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("query_results", query=form.search_query.data))

    return render_template("index.html", form=form)


@app.route("/search-results/<query>", methods=["GET"])
def query_results(query):
    print(os.environ.get("OMDB_API_KEY"))
    # return "Query"
    try:
        results = client.search(query)
    except ValueError as error_msg:
        return render_template("query_results.html", error_msg=error_msg)
    else:
        return render_template("query_results.html", results=results)


@app.route("/movies/<movie_id>", methods=["GET", "POST"])
def movie_detail(movie_id):
    return "movie_detail"


# Not a view function, used for creating a string for the current time.
def current_time() -> str:
    return datetime.now().strftime("%B %d, %Y at %H:%M:%S")

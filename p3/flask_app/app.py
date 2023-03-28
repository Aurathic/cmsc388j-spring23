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
app.config["MONGO_URI"] = ""
app.config['SECRET_KEY'] = ""

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

mongo = PyMongo(app)

client = MovieClient(os.environ.get('OMDB_API_KEY'))

# --- Do not modify this function ---
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for('query_results', query=form.search_query.data))

    return render_template('index.html', form=form)

@app.route('/search-results/<query>', methods=['GET'])
def query_results(query):
    try:
        results = client.search(query)
    except ValueError as error_msg:
        return render_template("query_results.html", error_msg=str(error_msg))
    else:
        return render_template("query_results.html", results=results)

@app.route('/movies/<movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    try:
        movie = client.retrieve_movie_by_id(movie_id)
    except ValueError as error_msg:
        return render_template("movie_detail.html", error_msg=str(error_msg))
    else:
        form = MovieReviewForm()
        if request.method == "POST":
            if form.validate_on_submit():
                review = {
                    "imdb_id": movie_id,
                    "commenter": form.name.data,
                    "content": form.text.data,
                    "date": current_time(),
                }
                mongo.db.reviews.insert_one(review)

        reviews = mongo.db.reviews.find({"imdb_id": movie_id})
        return render_template(
            "movie_detail.html", movie=movie, form=form, reviews=list(reviews)
        )


# Not a view function, used for creating a string for the current time.
def current_time() -> str:
    return datetime.now().strftime('%B %d, %Y at %H:%M:%S')
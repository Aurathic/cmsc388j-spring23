# 3rd-party packages
from flask import Flask, render_template, request, redirect, url_for
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
import os
from datetime import datetime

# local
from .client import MovieClient

app = Flask(__name__)
# app.config["MONGODB_HOST"] = "mongodb://localhost:27017/project_4"
app.config["MONGO_URI"] = open("./db.ini").readline()
app.config["SECRET_KEY"] = b"-\x87-\xa3\x02l\xc0\x02\xfe\xa2i\x8dS\x82y\xd4"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# Inject enumerate into project
@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)


@app.context_processor
def inject_round():
    return dict(round=round)


db = MongoEngine(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
bcrypt = Bcrypt(app)

# replace "default_value" with your api key if you need to hardcode it
client = MovieClient(os.getenv("OMDB_API_KEY", "29301fcf"))

from . import routes

from flask_login import UserMixin
from datetime import datetime
from . import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.objects(username=user_id).first()


class User(db.Document, UserMixin):
    email = db.EmailField(unique=True, required=True)
    username = db.StringField(unique=True, required=True)
    password = db.StringField()

    # Returns unique string identifying our object
    def get_id(self):
        self.username


class Review(db.Document):
    username = db.StringField(unique=True, required=True)
    review = db.StringField()

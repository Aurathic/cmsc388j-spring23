import os, io, base64, re
from flask_login import UserMixin
from datetime import datetime
from . import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.objects(username=user_id).first()


class User(db.Document, UserMixin):
    email = db.EmailField(unique=True, required=True)
    username = db.StringField(unique=True, required=True)
    password = db.StringField(required=True)
    profile_pic = db.ImageField()

    # Returns unique string identifying our object
    def get_id(self):
        return self.username

    def get_image(self):
        print(self.profile_pic)
        if self.profile_pic:
            file = self.profile_pic
        else:
            file = open("flask_app/static/images/default_profile_pic.png", "rb")
        image_bytes = io.BytesIO(file.read())
        image = base64.b64encode(image_bytes.getvalue()).decode()
        return image


class Review(db.Document):
    commenter = db.ReferenceField(User, required=True)
    content = db.StringField(required=True, min_length=5, max_length=500)
    date = db.StringField(required=True)
    imdb_id = db.StringField(required=True, min_length=9, max_length=9)
    movie_title = db.StringField(required=True, min_length=1, max_length=100)
    rating = db.IntField(min_value=1, max_value=5)

    # Returns unique string identifying our object
    def get_id(self):
        stripped_date = re.sub(r"[^A-Za-z0-9\-]", "", self.date)
        return f"{self.commenter.username}_{stripped_date}"

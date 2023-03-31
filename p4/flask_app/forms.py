from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import (
    StringField,
    IntegerField,
    SubmitField,
    TextAreaField,
    PasswordField,
    IntegerRangeField,
    RadioField,
)
from wtforms.validators import (
    InputRequired,
    DataRequired,
    NumberRange,
    Length,
    Email,
    EqualTo,
    ValidationError,
)
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
)

from .models import User, Review
from . import app, bcrypt, client


class SearchForm(FlaskForm):
    search_query = StringField(
        "Query", validators=[InputRequired(), Length(min=1, max=100)]
    )
    submit = SubmitField("Search")


class MovieReviewForm(FlaskForm):
    text = TextAreaField(
        "Comment", validators=[InputRequired(), Length(min=5, max=500)]
    )
    # rating = IntegerRangeField("Rating", validators=[NumberRange(1, 5)])
    rating = RadioField("Rating", choices=["No rating", 1, 2, 3, 4, 5])
    submit = SubmitField("Enter Comment")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=1, max=40)]
    )
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[InputRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.objects(username=username.data).first()
        if user is not None:
            raise ValidationError("Username is taken")

    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if user is not None:
            raise ValidationError("Email is taken")


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=1, max=40)]
    )
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Log In")

    def validate_username(self, username):
        user = User.objects(username=username.data).first()
        if user is None:
            raise ValidationError("Username does not exist.")

    def validate_password(self, password):
        user = User.objects(username=self.username.data).first()
        if user is not None and not bcrypt.check_password_hash(
            user.password, password.data
        ):
            raise ValidationError("Incorrect password.")


class UpdateUsernameForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=1, max=40)]
    )
    submit_username = SubmitField("Update")

    def validate_username(self, username):
        if username.data == current_user.username:
            raise ValidationError(
                "Your new username must be different from your old username."
            )
        user = User.objects(username=username.data).first()
        if user is not None:
            raise ValidationError("That username is taken.")


class UpdatePasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[InputRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[InputRequired(), EqualTo("password")]
    )
    submit_password = SubmitField("Update")


class UpdateProfilePicForm(FlaskForm):
    profile_pic = FileField(
        "Profile Picture",
        validators=[
            FileRequired(),
            FileAllowed(["jpg", "png"], "You can only upload PNG or JPGs."),
        ],
    )
    submit_profile_pic = SubmitField("Update")

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from ..models import User


def unique_email(form, field):
    if User.find_by_email(field.data):
        raise ValidationError('An account with this email already exists. Please log in instead.')


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired()])
    email = StringField("Email", validators=[InputRequired(), Email(), unique_email])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")

# Flask WT Forms
# https://hackersandslackers.com/flask-wtforms-forms/
# Form classes are Python models that determine the data our forms will capture,
# as well as the logic for validating whether or not a user has adequately completed
# a form when they attempt to submit
from flask_uploads import IMAGES
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileRequired
from wtforms.fields import EmailField, FileField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email, Length

class CheckUsernameAvailableForm(FlaskForm):
    """User Maintenance form."""
    username = StringField(
        'Username',
        [DataRequired()]
    )
    submit = SubmitField('Check')

class RegisterForm(FlaskForm):
    """User Maintenance form."""
    username = StringField(
        'Username',
        [DataRequired()]
    )
    password_hash = PasswordField(
        'Password Hash',
        [
            DataRequired(),
            Length(min=60,
            message=('Your password hash is too short.'))
        ]
    )
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    """User Maintenance form."""
    username = StringField(
        'Username',
        [DataRequired()]
    )
    password_hash = PasswordField(
        'Password Hash',
        [
            DataRequired(),
            Length(min=60,
            message=('Your password hash is too short.'))
        ]
    )
    submit = SubmitField('Login')

class UpdateUserForm(FlaskForm):
    """User Maintenance form."""
    username = StringField(
        'Username',
        [DataRequired()]
    )
    password_hash = PasswordField(
        'Password Hash',
        [
            DataRequired(),
            Length(min=60,
            message=('Your password hash is too short.'))
        ]
    )
    nickname = StringField(
        'Nickname',
        [
            DataRequired(),
            Length(min=4,
            message=('Your nickname is too short.'))
        ]
    )
    colour = StringField(
        'Colour',
        [
            DataRequired(),
            Length(min=6,
            message=('Your Html Colour Code is too short.'))
        ]
    )
    profile_picture = FileField(
        'Profile Picture',
        [
            FileAllowed(IMAGES, 'Unsupported File Type.')
        ]
    )
    submit = SubmitField('Update')

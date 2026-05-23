from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import InputRequired

class PostForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    content = TextAreaField("Markdown content", validators=[InputRequired()])
    tags = StringField("Tags (comma separated)")
    thumbnail = FileField("Thumbnail image", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])])
    submit = SubmitField("Post")

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Length, Optional, DataRequired

class ProfileEditForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500, message='Bio cannot exceed 500 characters.')
    ])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG, JPEG, and PNG images are allowed!')
    ])
    submit = SubmitField('Save Profile Changes')


class LearningInterestForm(FlaskForm):
    skill_name = StringField('Skill Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Skill name must be between 2 and 100 characters.')
    ])
    category = StringField('Category', validators=[
        Optional(),
        Length(max=50)
    ])
    submit = SubmitField('Add Interest')

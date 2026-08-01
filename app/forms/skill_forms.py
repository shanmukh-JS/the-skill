from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

PROFICIENCY_CHOICES = [
    ('Beginner', 'Beginner'),
    ('Intermediate', 'Intermediate'),
    ('Advanced', 'Advanced'),
    ('Expert', 'Expert')
]

CATEGORY_CHOICES = [
    ('Programming & Tech', 'Programming & Tech'),
    ('Languages', 'Languages'),
    ('Design & Art', 'Design & Art'),
    ('Music & Audio', 'Music & Audio'),
    ('Business & Finance', 'Business & Finance'),
    ('Fitness & Health', 'Fitness & Health'),
    ('Cooking & Crafts', 'Cooking & Crafts'),
    ('Academic & Science', 'Academic & Science'),
    ('Other', 'Other')
]

class SkillForm(FlaskForm):
    name = StringField('Skill Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Skill name must be between 2 and 100 characters.')
    ])
    category = SelectField('Category', choices=CATEGORY_CHOICES, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000, message='Description cannot exceed 1000 characters.')
    ])
    proficiency_level = SelectField('Proficiency Level', choices=PROFICIENCY_CHOICES, validators=[DataRequired()])
    submit = SubmitField('Save Skill')

from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class RequestForm(FlaskForm):
    skill_id = HiddenField('Skill ID', validators=[DataRequired()])
    message = TextAreaField('Message to Teacher (Optional)', validators=[
        Optional(),
        Length(max=500, message='Message cannot exceed 500 characters.')
    ])
    submit = SubmitField('Send Learning Request')


class RatingForm(FlaskForm):
    score = SelectField('Rating Score (1 to 5 Stars)', choices=[
        ('5', '5 Stars - Excellent'),
        ('4', '4 Stars - Good'),
        ('3', '3 Stars - Average'),
        ('2', '2 Stars - Poor'),
        ('1', '1 Star - Very Poor')
    ], validators=[DataRequired()])
    review_text = TextAreaField('Review / Feedback (Optional)', validators=[
        Optional(),
        Length(max=1000, message='Review text cannot exceed 1000 characters.')
    ])
    submit = SubmitField('Submit Rating & Review')

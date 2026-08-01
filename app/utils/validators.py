import re
from wtforms import ValidationError

def validate_password_complexity(form_or_password, field=None):
    if field is not None:
        password = field.data or ''
    else:
        password = str(form_or_password or '')

    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search(r'[A-Za-z]', password):
        raise ValidationError('Password must contain at least one letter.')
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one digit.')

def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg'}):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_image_stream(file_stream):
    if not file_stream:
        return False
    try:
        from PIL import Image
        img = Image.open(file_stream)
        img.verify()
        file_stream.seek(0)
        return img.format and img.format.lower() in ['jpeg', 'png', 'jpg']
    except Exception:
        if hasattr(file_stream, 'seek'):
            file_stream.seek(0)
        return False

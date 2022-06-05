import re
from forms import *
from wtforms.validators import ValidationError


def validate_phone(form, field):
    print('field', field.data)
    us_phone_num = '^([0-9]{3})[-][0-9]{3}[-][0-9]{4}$'
    match = re.search(us_phone_num, field.data)
    if not match:
        raise ValidationError('Error, phone number must be in format xxx-xxx-xxxx')

def validate_genres(form, field):
    print('field', field.data)
    if len(field.data) > 5:
        raise ValidationError('You can only choose 5 genres max.')


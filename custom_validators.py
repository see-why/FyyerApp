import sys
from xml.dom import ValidationErr
import phonenumbers


def validate_phone(field):
    if len(field.data) != 10:
        raise ValidationErr('Invalid phone number.')
    try:
        input_number = phonenumbers.parse(field.data)
        if not (phonenumbers.is_valid_number(input_number)):
            raise ValidationErr('Invalid phone number')
    except:
        print(sys.exc_info())
        raise ValidationErr('Invalid phone number')
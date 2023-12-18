from django.core.exceptions import ValidationError

def validate_discount_value(discount_type, discount_value):
    if discount_type == 'Percentage' and discount_value > 100:
        raise ValidationError('You cannot give more than 100 percent discount.')
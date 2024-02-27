from __future__ import annotations

from django.utils.timezone import datetime
from rest_framework.serializers import ValidationError


def get_shopping_cart_footer() -> str:
    time_format_message: str = 'Список создан в %H:%M от %d/%m/%Y'
    separate: str = '-' * len(time_format_message)
    return separate + '\n' + datetime.now().strftime(time_format_message)


def validate_input_value(
    value: int,
    field_name: str,
    error_message: str,
    limit_value: int = 1
) -> str | int:
    if value < limit_value:
        raise ValidationError({
            field_name: '{} {}.'.format(error_message, limit_value)
        })
    return value

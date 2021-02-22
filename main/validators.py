from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def validate_username(username):
    if User.objects.filter(**{'{}__iexact'.format(User.USERNAME_FIELD): username}).exists():
        raise ValidationError('User with this {} already exists'.format(User.USERNAME_FIELD))
    return username

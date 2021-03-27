import math

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from django.db.models import FileField, CharField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _


def validate_username(username):
    if User.objects.filter(**{'{}__iexact'.format(User.USERNAME_FIELD): username}).exists():
        raise ValidationError('User with this {} already exists'.format(User.USERNAME_FIELD))
    return username


def validate_matric(matric):
    if len(matric) != 9:
        raise forms.ValidationError(_('Matric number should be 8 characters long.'))

    try:
        matric_type = matric[0]
        year = int(matric[1:3])
        num = int(matric[1:8])
    except Exception:
        raise forms.ValidationError(_('Wrong matric number format, please double check.'))

    results = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "J",
        "K",
        "L",
        "ERROR",
    ]

    a_sum = 0

    if matric_type == "U":
        if year >= 17:
            weight = [6, 7, 4, 3, 8, 9, 2]
            offset = 4
        else:
            weight = [10, 7, 4, 3, 2, 9, 8]
            offset = 0
    elif matric_type == "B":
        weight = [10, 7, 4, 3, 2, 9, 8]
        offset = 9
    else:
        raise forms.ValidationError(_('Matric number should start with U or B'))

    for i in range(1, 8):
        a_sum += (num % 10) * weight[7 - i]
        num = math.floor(num / 10)

    a_sum += offset
    remainder = a_sum % 11

    result = results[remainder]

    if matric[8] == result:
        return True
    else:
        return False


def generate_matric(n=10):

    prefix = "U20"

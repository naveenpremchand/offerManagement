import string
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.utils.encoding import force_unicode
import httplib, urllib
import models
from django.core.exceptions import ObjectDoesNotExist
import datetime,re
from django.db.models.aggregates import Sum
from datetime import timedelta
from django.db.models import Q
import re
from decimal import Decimal


def check_none(value):
    return 0 if value is None else value


def person_in_group(groups):
    def decorator(func):
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if isinstance(user, AnonymousUser):
                path = request.build_absolute_uri()
                return redirect_to_login(path)
            group_list = map(str.strip, groups.split(','))
            if  bool(user.groups.filter(name__in=group_list).values('name')):
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("Access Denied")
        return _wrapped_view
    return decorator


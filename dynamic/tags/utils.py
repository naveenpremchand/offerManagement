from django.utils.encoding import force_unicode
import re
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from unityapp import models
from django.core.exceptions import ObjectDoesNotExist
from urlparse import parse_qs
from django import template
from django.template.defaultfilters import stringfilter
import datetime
import json
from reversion.models import Version
from django.http import Http404
register = template.Library()





@register.filter
def person_in_group(user, groups):
    
    if isinstance(user,AnonymousUser) :
        return False
        #group_list = force_unicode(groups).split(',')
    group_list = map(unicode.strip, groups.split(','))
    return bool(user.groups.filter(name__in=group_list).values('name'))



@register.filter(name='truncatechars')
@stringfilter
def truncatechars(value, arg):
    """
    Truncates a string after a certain number of chars.

    Argument: Number of chars to truncate after.
    """
    try:
        length = int(arg)
    except ValueError: # Invalid literal for int().
        return value # Fail silently.
    if len(value) > length:
        #return value[:length] + '...'
        return value[:length].rsplit(" ", 1)[0] + ' ...'
    return value
truncatechars.is_safe = True


@register.inclusion_tag('includes/field.html')
def render_field(field):
    return {'field': field}

@register.inclusion_tag('includes/field-common.html')
def render_field_common(form):
    return {'form': form}


@register.filter
def classname(obj):
    return obj.__class__.__name__

@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def formatted_no(num,format):
    return ('%'+'.%sd'%(format))%num


@register.filter(name='addcss')
def addcss(field, css):
   return field.as_widget(attrs={"class":css})


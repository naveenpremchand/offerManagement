from django import forms
from django.core.validators import validate_email
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


from .utils import get_user_model
from unityapp.models import *
import re
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
class PasswordRecoveryForm(forms.Form):
    username_or_email = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.case_sensitive = kwargs.pop('case_sensitive', True)
        super(PasswordRecoveryForm, self).__init__(*args, **kwargs)
        self.fields['username_or_email'].label = 'Username/Email'

    def clean_username_or_email(self):
        username = self.cleaned_data['username_or_email']
        if not EMAIL_REGEX.match(username):
            user_profile = UserProfile.multihost.filter(login_name=username)
            pass
        else:
            user_profile = UserProfile.multihost.filter(email__iexact=username)
            pass

        if not user_profile:
            raise forms.ValidationError(_("Sorry, User not found."))
            pass

        if not user_profile[0].email:
            raise forms.ValidationError(_("Sorry, Email not found for user."))
            pass

        if len(user_profile) > 1:
            raise forms.ValidationError(_("Sorry, Email found for more than one user.Please contact admin"))
            pass
        
        user = user_profile[0].user

        user_is_active = getattr(user, 'is_active', True)
        recovery_only_active_users = getattr(settings,
                                             'RECOVER_ONLY_ACTIVE_USERS',
                                             False)

        if recovery_only_active_users and not user_is_active:
            raise forms.ValidationError(_("Sorry, inactive users can't "
                                        "recover their password."))

        return username

    


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_('New password (confirm)'),
        widget=forms.PasswordInput,
    )

    error_messages = {
        'password_mismatch': _("The two passwords didn't match."),
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data['password2']
        if not password1 == password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch')
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['password1'])
        if commit:
            get_user_model()._default_manager.filter(pk=self.user.pk).update(
                password=self.user.password,
            )
        return self.user

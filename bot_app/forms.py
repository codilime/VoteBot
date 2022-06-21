from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_token(value: str) -> None:
    if value != settings.SLACK_VERIFICATION_TOKEN:
        raise ValidationError("Invalid Slack verification token.")


class ValidTokenForm(forms.Form):
    token = forms.CharField(validators=[validate_token])


class UserForm(ValidTokenForm):
    user_id = forms.CharField(required=True)


class TriggerForm(ValidTokenForm):
    trigger_id = forms.CharField(required=True)

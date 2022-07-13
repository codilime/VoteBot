from django import forms


class UserForm(forms.Form):
    user_id = forms.CharField(required=True)


class TriggerForm(forms.Form):
    trigger_id = forms.CharField(required=True)

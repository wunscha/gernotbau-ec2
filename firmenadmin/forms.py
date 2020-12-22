
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from superadmin.models import Firma

EigenerUser = get_user_model()
class MitarbeiterNeuForm(UserCreationForm):
    model = EigenerUser
    fields = [
        'first_name',
        'last_name',
        'password'
    ]

class MitarbeiterWählenForm(forms.Form):
    mitarbeiter = forms.ModelChoiceField(queryset = EigenerUser.objects.all())
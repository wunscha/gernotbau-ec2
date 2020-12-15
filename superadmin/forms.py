from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.forms import ModelForm
from .models import Firma

class FirmaNeuForm(ModelForm):
    class Meta:
        model = Firma
        fields = [
            'bezeichnung',
            'kurzbezeichnung',
            'adresse',
            'postleitzahl',
            'ort',
            'email_office'
        ]

EigenerUser = get_user_model()
class FirmenAdminNeuForm(UserCreationForm):
    class Meta:
        model = EigenerUser
        fields = ()

class ProjektNeuForm(forms.Form):
    bezeichnung = forms.CharField(max_length = 50)
    kurzbezeichnung = forms.CharField(max_length = 50)
    firma = forms.ModelChoiceField(
        queryset = Firma.objects.all(),
        label = 'Projektadmin-Firma'
        )
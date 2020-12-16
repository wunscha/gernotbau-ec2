from django import forms
from superadmin.models import Firma
from .models import Workflow_Schema

class FirmaNeuForm(forms.Form):
    firma = forms.ModelChoiceField(queryset = Firma.objects.all())

class WFSchWählenForm(forms.Form):
    wfsch = forms.ModelChoiceField(queryset = Workflow_Schema.objects.all())
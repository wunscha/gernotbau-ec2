from django import forms
from superadmin.models import Firma

class PrüffirmaNeuForm(forms.Form):
    firma = forms.ModelChoiceField(queryset = Firma.objects.all())
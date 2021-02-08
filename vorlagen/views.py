from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from superadmin.models import Projekt
from .models import V_Ordner, V_Ordner_Bezeichnung, V_Ordner_Freigabe_Lesen, V_Projektstruktur, V_Rolle, V_Ordner_Rolle

# Create your views here.
def test_ordner_view(request, db_bezeichnung):
    if request.method == 'POST':
        v_pjs = V_Projektstruktur.objects.using('default').get(pk = 1)
        v_pjs.ordnerstruktur_in_db_anlegen(db_bezeichnung_quelle = 'default', db_bezeichnung_ziel = db_bezeichnung)
    
    projekt = Projekt.objects.using('default').get(pk = db_bezeichnung)
    return render(request, './vorlagen/test_ordner.html', context = {'projekt': projekt})
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from projektadmin.models import V_Projektstruktur

# Create your views here.
def test_ordner_view(request, db_bezeichnung):
    if request.method == 'POST':
        v_pjs = V_Projektstruktur.objects.using('default').get(pk = 1)
            
        if request.POST['ereignis'] == 'ordnerstruktur_anlegen':
            v_pjs.ordnerstruktur_in_db_anlegen(db_bezeichnung_quelle = 'default', db_bezeichnung_ziel = db_bezeichnung)
    
        if request.POST['ereignis'] == 'workflowschemata_anlegen':
            v_pjs.workflowschemata_in_db_anlegen(db_bezeichnung_quelle = 'default', db_bezeichnung_ziel = db_bezeichnung)

    return render(request, './vorlagen/test_ordner.html', context = {'db_bezeichnung': db_bezeichnung})
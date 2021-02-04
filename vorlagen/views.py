from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from superadmin.models import Projekt
from .models import V_Ordner, V_Ordner_Bezeichnung, V_Ordner_Freigabe_Lesen, V_Rolle, V_Ordner_Rolle

# Create your views here.
def test_ordner_view(request, projekt_id):
    
    projekt = Projekt.objects.using('default').get(pk = projekt_id)
    v_ordner = V_Ordner.objects.using(projekt_id).get(pk = 1)
    v_rolle = V_Rolle.objects.using(projekt_id).get(pk = 1)
    

    if request.method == 'POST':
        
        if request.POST['ordnerbezeichnung']:
            update_v_ordner_bezeichnung = V_Ordner_Bezeichnung(
                bezeichnung = request.POST['ordnerbezeichnung'],
                v_ordner = v_ordner,
                zeitstempel = timezone.now()
                )
            update_v_ordner_bezeichnung.save(using = projekt_id)

        update_v_ordner_freigabe_lesen = V_Ordner_Freigabe_Lesen(
            v_ordner_rolle = V_Ordner_Rolle.objects.using(projekt_id).get(v_ordner = v_ordner, v_rolle = v_rolle),
            freigabe_lesen = True if 'freigabe_lesen' in request.POST else False,
            zeitstempel = timezone.now()
            )
        update_v_ordner_freigabe_lesen.save(using = projekt_id)

    # Belade Context und rendere Template
    ordnerbezeichnung = v_ordner.bezeichnung(projekt)
    lesefreigabe = v_ordner.freigabe_lesen(projekt, v_rolle)
    context = {
        'projekt': projekt.__dict__,
        'ordnerbezeichnung': ordnerbezeichnung,
        'lesefreigabe': lesefreigabe
        }

    return render(request, './vorlagen/test_ordner.html', context)
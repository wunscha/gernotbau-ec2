from django.shortcuts import render
from .models import TEST_Dokument
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponseRedirect

def test_dokumente(request, projekt_id):
    # Request=POST: Lege neues Dokument an
    if request.method == 'POST':
        # Dokumententebezeichnung aus POST holen
        bezeichnung = request.POST['dokument_bezeichnung']
        # Mitarbeiter ID holen
        mitarbeiter_id = request.user.id

        # Dokument in DB anlegen
        neues_dokument = TEST_Dokument(
            bezeichnung = bezeichnung,
            mitarbeiter_id = mitarbeiter_id
        )
        neues_dokument.save(using = projekt_id)

        # Weiterleitung zur Übersicht
        return HttpResponseRedirect(reverse('test_multidb:test_dokumente', args=(projekt_id)))


    # Request!= POST: Zeige Dokumente für Projekt
    else:
        alle_dokumente = TEST_Dokument.objects.using(projekt_id).all()

        # liste_dokumente für context befüllen
        liste_dokumente = []
        for dokument in alle_dokumente:
            # Dict für Dokument anlegen
            dict_dokument = {}

            # Dict befüllen
            dict_dokument['dokument_id'] = dokument.id
            dict_dokument['bezeichnung'] = dokument.bezeichnung
            dict_dokument['zeit_erstellung'] = dokument.zeit_erstellung

            # Benutzer aus Benutzer-DB holen
            User = get_user_model()
            mitarbeiter_id = dokument.mitarbeiter_id
            mitarbeiter = User.objects.get(pk = mitarbeiter_id)
            dict_dokument['mitarbeiter'] = mitarbeiter.first_name + ' ' + mitarbeiter.last_name

            liste_dokumente.append(dict_dokument)

        # context befüllen und Template laden
        context = {
            'projekt_id': projekt_id,
            'liste_dokumente': liste_dokumente,
        }

        return render(request, 'test_multidb_dokumente.html', context)
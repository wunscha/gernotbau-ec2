from gernotbau.settings import DB_SUPER
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.urls import reverse
from funktionen import hole_dicts
from projektadmin.models import liste_projekte_mitarbeiter
from kommunikation.models import Nachricht_Empfänger

def home_view(request):
    
    # Prüfung Login
    if not request.user.is_authenticated:
        return render(request, './registration/login.html')
    else:
        # Wenn Firmenadmin Weiterleitung zu Firmenadmin-Bereich
        # if request.user.ist_firmenadmin:
        #    return HttpResponseRedirect(reverse('firmenadmin:übersicht_mitarbeiter', args=[request.user.firma_id]))
        # else:

        # Projekte holen
        li_pj = []
        for pj in liste_projekte_mitarbeiter(request.user):
            dict_pj = pj.__dict__
            dict_pj['bezeichnung'] = pj.bezeichnung()
            li_pj.append(dict_pj)

        # Neue Nachrichten zählen
        anzahl_nr_neu = 0
        qs_nr_empf = Nachricht_Empfänger.objects.using(DB_SUPER).filter(empfänger = request.user)
        for nr_empf in qs_nr_empf:
            if not nr_empf._gelesen():
                anzahl_nr_neu += 1

        context={
            'liste_projekte_user_projektadmin': '',
            'liste_projekte_user': li_pj,
            'anzahl_neue_nachrichten': anzahl_nr_neu
        }

        return render(request, 'home.html', context)

def login_view(request):

    # Wenn POST: User authentifizieren und einloggen und Weiterleitung zu Home
    if request.method == 'POST':
        # User authentifizieren
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password) # Gibt User-Objekt zurück, wenn Daten vorhanden
        
        # Wenn user in DB vorhanden: Log in
        if user is not None:
            login(request, user)
        
            # Weiterleitung zu Home:
            return HttpResponseRedirect(reverse('home'))

        # Wenn user nicht vorhanden: Formular neu laden
        else:
            # Anzeige Fehlermeldung, wenn Login fehlgeschlagen
            context = {'fehlermeldung': 'Sie konnten nicht eingeloggt werden'}
            return render(request, './registration/login.html', context)

    # Wenn GET etc.: Zeige Login-Formular
    else:
        return render(request, './registration/login.html')
from datetime import time
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Firma, Projekt, Mitarbeiter, Projekt_Firma, Firma_Ist_Projektadmin
from projektadmin.models import Ordner, Ordner_Firma_Freigabe, Rolle, Pfad
from funktionen import emailfunktionen
from funktionen.datenbank import lege_datenbank_an
from projektadmin.views import zugriff_verweigert_projektadmin
from projektadmin.funktionen import user_ist_projektadmin
from gernotbau.settings import DB_SUPER

'''
def zugriff_verweigert_superadmin(request, projekt_id):
    if not request.user.ist_superadmin:
        fehlermeldung = 'Loggen Sie sich bitte als Superadmin ein'
        context = {'fehlermeldung': fehlermeldung}
        return render(request, './registration/login.html', context)

def firma_neu_view(request):
    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # Prüfung Superadmin oder Projektadmin
    if not request.user.ist_superadmin:
        if request.method == 'POST':
            if not user_ist_projektadmin(request.user, request.POST['projekt_id']):
                # Fehlermeldung
                fehlermeldung = 'Bitte loggen Sie sich als Superadmin oder Projektadmin ein'
                context = {'fehlermeldung':fehlermeldung}
                return render(request, './registration/login.html', context)
        else:
            # Fehlermeldung
            fehlermeldung = 'Bitte loggen Sie sich als Superadmin oder Projektadmin ein'
            context = {'fehlermeldung':fehlermeldung}
            return render(request, './registration/login.html', context)
    

    if request.method == 'POST':
        if request.POST['ereignis'] == 'firma_neu':
            # Neue Firma anlegen
            neue_firma = Firma.objects.using('default').create(
                zeitstempel = timezone.now()
                )
            neue_firma.entlöschen
            neue_firma.bezeichnung_ändern('default', request.POST['bezeichnung'])
            neue_firma.kurzbezeichnung_ändern('default', request.POST['kurzbezeichnung'])
            neue_firma.strasse_ändern('default', request.POST['strasse'])
            neue_firma.hausnummer_ändern('default', request.POST['hausnummer'])
            neue_firma.postleitzahl_ändern('default', request.POST['postleitzahl'])
            neue_firma.email_ändern('default', request.POST['email'])
            neue_firma.entlöschen('default')

            # Rollen festlegen
            if 'rolle_id' in request.POST:
                db_projekt = Projekt.objects.using('default').get(pk = request.POST['projekt_id']).db_bezeichnung('default')
                for r_id in request.POST['rolle_id']:
                    r = Rolle.objects.using(db_projekt).get(pk = r_id)
                    r.firma_zuweisen(db_projekt, neue_firma)

            # Firmenadmin anlegen
            User = get_user_model()
            neuer_mitarbeiter = User(
                firma = neue_firma,
                zeitstempel = timezone.now(),
                username = request.POST['email'],
                password = make_password(request.POST['passwort'])
                )
            neuer_mitarbeiter.save(using = 'default')
            neuer_mitarbeiter.entlöschen('default')
            neuer_mitarbeiter.firmenadmin_ernennen('default')
            neuer_mitarbeiter.superadmin_entheben('default')

            # Erfolgsmeldung
            erfolgsmeldung = 'Neue Firma "' + neue_firma.bezeichnung('default') + '" wurde angelegt'

    # Wenn GET etc.: context leer
    else:
        erfolgsmeldung = ''
        
    # Formular laden
    context = {
        'erfolgsmeldung': erfolgsmeldung,
        }
    return render(request, './superadmin/firma_neu.html') 
        
    '''

def projekt_neu_view(request):
    # TODO: 'default' und nicht DB_SUPER als DB-Bezeichnung wegen zirkulärem Import --> schöner lösen
    
    if request.method == 'POST':
        # Neues Projekt anlegen
        neues_projekt = Projekt.objects.using(DB_SUPER).create(zeitstempel = timezone.now())
        neues_projekt.bezeichnung_ändern(neue_bezeichnung = request.POST['bezeichnung'])
        neues_projekt.kurzbezeichnung_ändern(neue_kurzbezeichnung = request.POST['kurzbezeichnung'])
        
        neue_db_bezeichnung = 'pj_' + str(neues_projekt.id)
        neues_projekt.db_bezeichnung_ändern(neue_db_bezeichnung)
        lege_datenbank_an(db_bezeichnung = neues_projekt.db_bezeichnung())

        # Projektadmin-Firma zuordnen
        firma = Firma.objects.using(DB_SUPER).get(pk = request.POST['firma_id'])
        projekt_firma_neu = Projekt_Firma.objects.using(DB_SUPER).create(
            projekt = neues_projekt,
            firma = firma,
            zeitstempel = timezone.now()
            )
        projekt_firma_neu.aktualisieren()
        
        Firma_Ist_Projektadmin.objects.using(DB_SUPER).create(
            projekt_firma = projekt_firma_neu,
            ist_projektadmin = True,
            zeitstempel = timezone.now()
            )

        Pfad.objects.using(neues_projekt.db_bezeichnung()).create(
            pfad = neues_projekt.id,
            zeitstempel = timezone.now()
            )

    # Liste Firmen für context
    liste_firmen_objekte = Firma.objects.using(DB_SUPER).all()
    liste_firmen = []
    for firma in liste_firmen_objekte:
        dict_firma = {}
        dict_firma['id'] = firma.id
        dict_firma['kurzbezeichnung'] = firma._kurzbezeichnung()
        liste_firmen.append(dict_firma)

    # Formular laden
    context={
        'liste_firmen': liste_firmen,
        }
    return render(request, './superadmin/projekt_neu.html', context)
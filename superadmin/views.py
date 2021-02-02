from django.shortcuts import render
from .models import Firma, Projekt, Projekt_Firma_Mail
from projektadmin.models import Ordner, Ordner_Firma_Freigabe
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.urls import reverse
from funktionen import emailfunktionen

def firma_neu_view(request):
    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    else:

        # Prüfung Superadmin
        if not request.user.ist_superadmin:
            # Fehlermeldung
            fehlermeldung = 'Bitte loggen Sie sich als Superadmin ein'
            context = {'fehlermeldung':fehlermeldung}
            return render(request, './registration/login.html', context)
            
        else:
            # Wenn POST: Lege neue Firma inkl. Firmenadmin an
            if request.method == 'POST':
                
                # Email-Adresse generieren
                email = emailfunktionen.generiere_email_adresse_fa(kurzbezeichnung = request.POST['kurzbezeichnung'])

                # Neue Firma anlegen
                neue_firma = Firma(
                    bezeichnung = request.POST['bezeichnung'],
                    kurzbezeichnung = request.POST['kurzbezeichnung'],
                    strasse = request.POST['strasse'],
                    hausnummer = request.POST['hausnummer'],
                    postleitzahl = request.POST['postleitzahl'],
                    ort = request.POST['ort'],
                    email_office = request.POST['email_office'],
                    email = email,
                )
                neue_firma.save(using='default')

                # Firmenadmin anlegen
                User = get_user_model()
                neuer_firmenadmin = User(
                    firma = neue_firma,
                    ist_firmenadmin = True,
                    first_name = email,
                    username = email, 
                    password = make_password(request.POST['passwort']), # Erzeugt gehashtes Passwort für DB
                )
                neuer_firmenadmin.save(using='default')

                # TODO: Log-Einträge
                # TODO: Infomails

                # Erfolgsmeldung für context
                erfolgsmeldung = 'Firma "' + neue_firma.bezeichnung + '" wurde angelegt'

            # Wenn GET etc.: context leer
            else:
                erfolgsmeldung = ''
                
            # Formular laden
            context = {
                'erfolgsmeldung': erfolgsmeldung,
                }
            return render(request, './superadmin/firma_neu.html') 
        

def projekt_neu_view(request):
    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Superadmin
        if not request.user.ist_superadmin:
            # Fehlermeldung
            fehlermeldung = 'Bitte loggen Sie sich als Superadmin ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)

        else:
            # Wenn POST: Neues Projekt anlegen
            if request.method == 'POST':
                # Neues Projekt anlegen
                neues_projekt = Projekt(
                    bezeichnung = request.POST['bezeichnung'],
                    kurzbezeichnung = request.POST['kurzbezeichnung']
                )
                neues_projekt.save(using='default')

                # Projektadmin-Firma zuordnen
                firma = Firma.objects.using('default').get(pk = request.POST['firma_id'])
                neu_projekt_firma_mail = Projekt_Firma_Mail(
                    ist_projektadmin = True,
                    email = neues_projekt.kurzbezeichnung + '@gernotbau.at',
                    firma = firma,
                    projekt = neues_projekt,
                )
                neu_projekt_firma_mail.save(using='default')

                '''
                # Root Ordner anlegen
                root_ordner = Ordner(
                    bezeichnung = 'ROOT',
                    ist_root_ordner = True,
                )
                root_ordner.save(using = str(neues_projekt.id))

                # Ordnerberechtigung Root-Ordner <-> Projektadmin-Firma anlegen
                neu_ordner_firma_freigabe = Ordner_Firma_Freigabe(
                    ordner = root_ordner,
                    firma_id = firma.id,
                    freigabe_lesen = True,
                    freigabe_upload = True,
                    freigaben_erben = False
                )
                neu_ordner_firma_freigabe.save(using = str(neues_projekt.id))
                '''

                # TODO: Log-Einträge
                # TODO: InfoMails
                # TODO: ROOT-Ordner anlegen (inkl. Freigabe für Projektadmin Firma --> dafür muss DB-Verbindung aber schon bestehen)

                # Erfolgsmeldung für context
                erfolgsmeldung = 'Projekt "' + neues_projekt.bezeichnung + '"wurde angelegt.'

            # Wenn GET etc.: erfolgsmeldung leer
            else:
                erfolgsmeldung = ''
        
        # Liste Firmen für context
        liste_firmen_objekte = Firma.objects.using('default').all()
        liste_firmen = []
        for firma in liste_firmen_objekte:
            dict_firma = {}
            dict_firma['id'] = firma.id
            dict_firma['kurzbezeichnung'] = firma.kurzbezeichnung
            liste_firmen.append(dict_firma)

        # Formular laden
        context={
            'erfolgsmeldung': erfolgsmeldung,
            'liste_firmen': liste_firmen,
            }
        return render(request, './superadmin/projekt_neu.html', context)
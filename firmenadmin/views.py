from django.shortcuts import render
from django.contrib.auth import get_user_model
from superadmin.models import Mitarbeiter, Projekt_Mitarbeiter_Mail, Projekt_Firma_Mail, Projekt
from projektadmin.models import Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Mitarbeiter
from django.http import HttpResponse, HttpResponseRedirect
from .forms import MitarbeiterNeuForm
from django.urls import reverse
from funktionen import hole_dicts, emailfunktionen
from django.contrib.auth.hashers import make_password

def übersicht_mitarbeiter_view(request):

    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        #Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)
        else:
            # POST: Ereignis Abfragen (= Vorarbeit für etwaige Erweiterungen):
            if request.method == 'POST':
                if request.POST['ereignis'] == 'mitarbeiter_löschen':
                    löschkandidat = Mitarbeiter.objects.using('default').get(pk = request.POST['mitarbeiter_löschen_id'])
                    löschkandidat.aktiv = False
                    löschkandidat.save(using = 'default')

                    # TODO: InfoMail
                    # TODO: Verknüpfungen löschen

            liste_mitarbeiter = hole_dicts.firmenmitarbeiter(firma = request.user.firma)
            context = {'liste_mitarbeiter': liste_mitarbeiter}
            return render(request, './firmenadmin/übersicht_mitarbeiter.html', context)
    
def mitarbeiter_neu_view(request):

    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)

        else:
            # POST: Neuen Mitarbeiter anlegen
            neuer_mitarbeiter = None # Vorbereitung für context
            if request.method == 'POST':
                
                # E-Mail-Adresse generieren (inkl. Kontrolle ob Adresse schon vorhanden)
                email = emailfunktionen.generiere_email_adresse_ma(
                    firma = request.user.firma, 
                    nachname = request.POST['nachname']
                    )

                User = get_user_model()
                neuer_mitarbeiter = User(
                    first_name = request.POST['vorname'],
                    last_name = request.POST['nachname'],
                    password = make_password(request.POST['passwort']), # Erzeugt gehashtes Passwort
                    firma = request.user.firma,
                    email = email,
                    username = email,
                    ist_firmenadmin = False, 
                    ist_superadmin = False
                )

                neuer_mitarbeiter.save(using = 'default')

            # context packen und Bestätigungsseite laden
            dict_neuer_mitarbeiter = neuer_mitarbeiter.__dict__ if neuer_mitarbeiter else None
            
            context = {'neuer_mitarbeiter': dict_neuer_mitarbeiter}
            return render(request, './firmenadmin/mitarbeiter_neu.html', context)

def übersicht_projekte_view(request):

    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './firmenadmin/login.html', context)
        else:
            if request.method == 'POST':
                # Mitarbeiter zu Projekt hinzufügen
                if request.POST['ereignis'] == 'mitarbeiter_hinzufügen':
                    mitarbeiter_hinzu = Mitarbeiter.objects.using('default').get(pk = request.POST['mitarbeiter_id'])
                    projekt = Projekt.objects.using('default').get(pk = request.POST['projekt_id'])
                    neuer_eintrag_pj_ma_mail = Projekt_Mitarbeiter_Mail(
                        mitarbeiter = mitarbeiter_hinzu,
                        projekt = projekt,
                        email = projekt.kurzbezeichnung + '.' + mitarbeiter_hinzu.email, # TODO: evtl. in 'generiere-Email' Funktion auslagern
                        ist_projektadmin = False
                    )
                    neuer_eintrag_pj_ma_mail.save(using = 'default')
                
                # TODO: InfoMails
                # TODO: Logs
                
                # Mitarbeiter von Projekt lösen
                elif request.POST['ereignis'] == 'mitarbeiter_lösen':
                    mitarbeiter_lösen = Mitarbeiter.objects.using('default').get(pk = request.POST['mitarbeiter_id'])
                    projekt = Projekt.objects.using('default').get(pk = request.POST['projekt_id'])
                    eintrag_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').get(mitarbeiter = mitarbeiter_lösen, projekt = projekt)
                    eintrag_pj_ma_mail.delete(using = 'default')
                
                # TODO: InfoMails
                # TODO: Logs (aktiv/inaktiv?)
                # TODO: Kontrolle, ob Prüfer für WFSch

                # Projektadmin wählen
                elif request.POST['ereignis'] == 'projektadmin_wählen':
                    mitarbeiter_gewählt = Mitarbeiter.objects.using('default').get(pk = request.POST['mitarbeiter_id'])
                    projekt = Projekt.objects.using('default').get(pk = request.POST['projekt_id'])
                    eintrag_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').get(mitarbeiter = mitarbeiter_gewählt, projekt = projekt)
                    eintrag_pj_ma_mail.ist_projektadmin = True
                    eintrag_pj_ma_mail.save(using = 'default')

                # Projektadmin abwählen
                elif request.POST['ereignis'] == 'projektadmin_abwählen':
                    mitarbeiter_abgewählt = Mitarbeiter.objects.using('default').get(pk = request.POST['mitarbeiter_id'])
                    projekt = Projekt.objects.using('default').get(pk = request.POST['projekt_id'])
                    eintrag_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').get(mitarbeiter = mitarbeiter_abgewählt, projekt = projekt)
                    eintrag_pj_ma_mail.ist_projektadmin = False
                    eintrag_pj_ma_mail.save(using = 'default')

            # context packen und Übersich laden
            liste_projekte = hole_dicts.liste_projekte_firma(firma = request.user.firma)
            context = {'liste_projekte': liste_projekte}
            
            return render(request, './firmenadmin/übersicht_projekte.html', context)

def übersicht_wfsch_view(request):
    
    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './firmenadmin/login.html', context)
        else:
            if request.method == 'POST':
                projekt_id = request.POST['projekt_id']

                # Ereignis 'Prüfer hinzufügen'
                if request.POST['ereignis'] == 'prüfer_hinzufügen':
                    wfsch_stufe = Workflow_Schema_Stufe.objects.using(projekt_id).get(pk = request.POST['wfsch_stufe_id'])
                    neuer_eintrag_wfsch_stufe_ma = WFSch_Stufe_Mitarbeiter(
                        immer_erforderlich = False,
                        wfsch_stufe = wfsch_stufe, 
                        mitarbeiter_id = request.POST['prüfer_hinzufügen_id']
                        )
                    neuer_eintrag_wfsch_stufe_ma.save(using = projekt_id)

                    # TODO: InfoMails
                    # TODO: Logs

                # Ereignis 'Erforderlichkeit ändern'
                if request.POST['ereignis'] == 'erforderlichkeit_ändern':
                    wfsch_stufe = Workflow_Schema_Stufe.objects.using(projekt_id).get(pk = request.POST['wfsch_stufe_id'])
                    eintrag_wfsch_stufe_ma = WFSch_Stufe_Mitarbeiter.objects.using(projekt_id).get(wfsch_stufe = wfsch_stufe, mitarbeiter_id = request.POST['prüfer_id'])
                    
                    # Einstellung für 'immer erforderlich' ändern
                    eintrag_wfsch_stufe_ma.immer_erforderlich = True if eintrag_wfsch_stufe_ma.immer_erforderlich == False else False
                    eintrag_wfsch_stufe_ma.save(using = projekt_id)

                # Ereignis 'Prüfer entfernen'
                if request.POST['ereignis'] == 'prüfer_lösen':
                    wfsch_stufe = Workflow_Schema_Stufe.objects.using(projekt_id).get(pk = request.POST['wfsch_stufe_id'])
                    eintrag_wfsch_stufe_ma = WFSch_Stufe_Mitarbeiter.objects.using(projekt_id).get(wfsch_stufe = wfsch_stufe, mitarbeiter_id = request.POST['prüfer_id'])
                    eintrag_wfsch_stufe_ma.delete(using = projekt_id)

                    # TODO: InfoMails
                    # TODO: Logs
                    # TODO: Kontrolle bestehenden Worfklows + Warnhinweis                    

        # context packen und Bestätigungsseite laden
        li_wfsch = hole_dicts.liste_wfsch_firma(firma = request.user.firma)

        # li_wfsch um Angaben erweitern, ob userfirma Prüffirma ist
        for wfsch in li_wfsch:
            for wfsch_st in wfsch['liste_wfsch_stufen']:
                # Angabe 'userfirma_ist_prüffirma' auf Stufenebene einfügen
                wfsch_st['userfirma_ist_prüffirma'] = False
                
                for prüffirma in wfsch_st['liste_prüffirmen']:
                    # Angabe 'ist_userfirma' auf Firmenebene einfügen
                    prüffirma['ist_userfirma'] = False
                    
                    # Werte anpassen
                    if prüffirma['id'] == request.user.firma.id:
                        prüffirma['ist_userfirma'] = True
                        wfsch_st['userfirma_ist_prüffirma'] = True

        
        context = {'li_wfsch': li_wfsch}
        return render(request, './firmenadmin/übersicht_wfsch.html', context)

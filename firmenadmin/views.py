from gernotbau.settings import DB_SUPER
from django.shortcuts import render
from django.contrib.auth import get_user_model
from superadmin.models import Mitarbeiter, Projekt_Mitarbeiter, Projekt, Firma
from projektadmin.models import Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Mitarbeiter, liste_rollen_firma_dict
from django.http import HttpResponse, HttpResponseRedirect
from .forms import MitarbeiterNeuForm
from django.urls import reverse
from funktionen import hole_dicts, emailfunktionen
from django.contrib.auth.hashers import make_password

def übersicht_mitarbeiter_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin

    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    # POST
    if request.method == 'POST':
        # EREIGNIS MITARBEITER LÖSCHEN
        if request.POST['ereignis'] == 'mitarbeiter_löschen':
            User = get_user_model()
            User.objects.using(DB_SUPER).get(pk = request.POST['mitarbeiter_id']).löschen()

    # Pakte Context und Lade Template
    context = {
        'firma': firma.firma_dict(),
        'liste_mitarbeiter': firma.liste_mitarbeiter()
        }
    return render(request, './firmenadmin/übersicht_mitarbeiter.html', context)

    '''
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
    '''

def mitarbeiter_anlegen_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    # POST
    if request.method == 'POST':
        # EREIGNIS MITARBEITER ANLEGEN
        if request.POST['ereignis'] == 'mitarbeiter_anlegen':
            firma.mitarbeiter_anlegen(DB_SUPER, formulardaten = request.POST)

    # Packe Context und Lade Template
    li_projekte = []
    for pj in firma.liste_projekte():
        dict_pj = pj.projekt_dict()
        dict_pj['liste_rollen'] = liste_rollen_firma_dict(pj.db_bezeichnung(), firma)
        li_projekte.append(dict_pj)

    context = {
        'firma': firma,
        'liste_projekte': li_projekte
        }
    return render(request, './firmenadmin/mitarbeiter_anlegen.html', context)

    '''
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
    '''

def übersicht_projekte_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin

    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    # Packe Context und lade Template
    li_projekte_dicts = []
    for projekt in firma.liste_projekte():
        dict_projekt = projekt.projekt_dict()
        dict_projekt['liste_rollen'] = liste_rollen_firma_dict(projekt, firma)
        dict_projekt['liste_projektmitarbeiter'] = firma.liste_mitarbeiter_projekt_dict(projekt)
        dict_projekt['firma_ist_projektadmin'] = firma.ist_projektadmin(projekt)
        li_projekte_dicts.append(dict_projekt)

    context = {
        'firma': firma,
        'liste_projekte': li_projekte_dicts, 
        }
    
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

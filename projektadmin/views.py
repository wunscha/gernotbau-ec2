from django.shortcuts import render

import funktionen
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import Ordner_WFSch, Projektstruktur, V_Workflow_Schema, WFSch_Stufe_Rolle, Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Firma, Ordner, Ordner_Firma_Freigabe
from .forms import FirmaNeuForm, WFSchWählenForm
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.utils import timezone

from superadmin.models import Projekt, Firma
from projektadmin.models import V_Projektstruktur, Rolle, liste_rollen_dict, liste_rollen, liste_rollen_firma, liste_rollen_firma_dict, liste_ordner_dict, liste_ordner, liste_wfsch_dict, liste_v_pjs_dict, firma_projektrollen_zuweisen
from funktionen import hole_objs, hole_dicts, workflows, ordnerfunktionen
from gernotbau.settings import DB_SUPER

def zugriff_verweigert_projektadmin(request, projekt_id):
    if not user_ist_projektadmin(request.user, projekt_id):
        fehlermeldung = 'Melden Sie sich bitte als Projektadmin für das gewünschte Projekt an'
        context = {'fehlermeldung': fehlermeldung}
        return render(request, './registration/login.html', context)

################################################
# Firmenverwaltung

def firma_anlegen_view(request, projekt_id):
    # TODO: Kontrolle LogIn
    # TODO: Kontrolle Projektadmin
    
    projekt = Projekt.objects.using('default').get(pk = projekt_id)
    erfolgsmeldung = ''

    # POST
    if request.method == 'POST':
        neue_firma = projekt.firma_anlegen(formulardaten = request.POST, ist_projektadmin = False)
        firma_projektrollen_zuweisen(projekt, firma = neue_firma, formulardaten = request.POST)
        erfolgsmeldung = 'Firma "' + neue_firma.bezeichnung() + '" wurde angelegt.'

        return HttpResponseRedirect(reverse('projektadmin:übersicht_firmen', args = [projekt_id]))

    # Packe Context und Lade Template
    context = {
        'liste_rollen': liste_rollen_dict(projekt),
        'projekt_id': projekt_id,
        'erfolgsmeldung': erfolgsmeldung
        }
    return render(request, './projektadmin/firma_anlegen.html', context)

def übersicht_firmen_view(request, projekt_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    
    # POST
    if request.method == 'POST':
        
        # EREIGNIS FIRMA HINZUFÜGEN
        if request.POST['ereignis'] == 'firma_hinzufügen':
            fa = Firma.objects.using(DB_SUPER).get(pk = request.POST['firma_id'])
            projekt.firma_verbinden(firma = fa)

        # EREIGNIS FIRMA LÖSEN
        if request.POST['ereignis'] == 'firma_lösen':
            fa = Firma.objects.using(DB_SUPER).get(pk = request.POST['firma_id'])
            projekt.firma_lösen(firma = fa)

    # Packe Context und Lade Template
    context = {
        'projekt_id': projekt_id,
        'liste_projektfirmen': projekt.liste_projektfirmen_dicts(),
        'liste_nicht_projektfirmen': projekt.liste_nicht_projektfirmen_dicts(),
        }

    return render(request, './projektadmin/übersicht_firmen.html', context)

def detailansicht_firma_view(request, projekt_id, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)
    
    # POST
    if request.method == 'POST':
        
        # EREIGNIS ROLLEN AKTUALISIEREN
        if request.POST['ereignis'] == 'rollen_aktualisieren':
            firma_projektrollen_zuweisen(projekt, firma, formulardaten = request.POST)
            '''
            for r in liste_rollen(db_projekt):
                ist_firmenrolle = True if str(r.id) in request.POST else False
                r.ist_firmenrolle_ändern(db_projekt, firma, ist_firmenrolle)
            '''

        # EREIGNIS IST FIRMENADMIN AKTUALISIEREN
        if request.POST['ereignis'] == 'ist_projektadmin_aktualisieren':
            ist_projektadmin = True if 'ist_projektadmin' in request.POST else False
            firma.ist_projektadmin_ändern(DB_SUPER, projekt, ist_projektadmin)

    # Liste Rollen
    li_rollen_dict = []
    for r in liste_rollen(projekt):
        dict_r = r.dict_rolle(projekt)
        dict_r['ist_firmenrolle'] = r.ist_firmenrolle(projekt, firma)
        li_rollen_dict.append(r)
    
    # Packe Context und Lade Template
    context = {
        'projekt_id': projekt_id,
        'liste_rollen': li_rollen_dict,
        'firma': firma.firma_dict(),
        'firma_ist_projektadmin': firma.ist_projektadmin(projekt)
        }

    return render(request, './projektadmin/detailansicht_firma.html', context)

################################################
# WFSch-Verwaltung

# NEUE VIEW (11.02.2021)
def übersicht_wfsch_view(request, projekt_id):
    # TODO: Kontrolle LogIn
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using('default').get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung()
    kontrolle = 0

    # POST
    if request.method == 'POST':
        # EREIGNIS PRÜFFIRMA HINZUFÜGEN
        if request.POST['ereignis'] == 'prüffirma_hinzufügen':
            rolle = Rolle.objects.using(db_projekt).get(pk = request.POST['rolle_id'])
            wfsch_stufe = WFSch_Stufe.objects.using(db_projekt).get(pk = request.POST['wfsch_stufe_id'])
            prüffirma = Firma.objects.using(DB_SUPER).get(pk = request.POST['prüffirma_id'])
            wfsch_stufe.prüffirma_hinzufügen(projekt, rolle = rolle, firma = prüffirma)

        # EREIGNIS PRÜFFIRMA LÖSEN
        if request.POST['ereignis'] == 'prüffirma_lösen':
            rolle = Rolle.objects.using(db_projekt).get(pk = request.POST['rolle_id'])
            wfsch_stufe = WFSch_Stufe.objects.using(db_projekt).get(pk = request.POST['wfsch_stufe_id'])
            wfsch_stufe.prüffirma_lösen(projekt, rolle = rolle, firma_id = request.POST['prüffirma_id'])

        # EREIGNIS WFSCH LÖSCHEN
        if request.POST['ereignis'] == 'wfsch_löschen':
            wfsch = Workflow_Schema.objects.using(db_projekt).get(pk = request.POST['wfsch_id'])
            wfsch.löschen(projekt)

        # EREIGNIS WFSCH VORLAGE ANLEGEN
        if request.POST['ereignis'] == 'wfsch_vorlage_anlegen':
            v_wfsch = V_Workflow_Schema.objects.using(DB_SUPER).get(pk = request.POST['v_wfsch_id'])
            v_wfsch.in_db_anlegen(projekt)

        # TODO: EREIGNIS STUFE HINZUFÜGEN/ENTFERNEN IMPLEMENTIEREN
        # TODO: EREIGNIS ROLLE HINZUFÜGEN/ENTFERNEN IMPLEMENTIEREN
        # TODO: EREIGNIS WFSCH HINZUFÜGEN/ENTFERNEN IMPLEMENTIEREN

        # EREIGNIS FIRMEN NACH ROLLEN ZUWEISEN
        if request.POST['ereignis'] == 'firmen_nach_rollen_zuweisen':
            
            wfsch = Workflow_Schema.objects.using(db_projekt).get(pk = request.POST['wfsch_id'])
            for s in wfsch.liste_stufen(projekt):
                for r in s.liste_rollen(projekt):
                    for f in projekt.liste_projektfirmen():
                        if r in liste_rollen_firma(projekt, f):
                            kontrolle += 1
                            s.prüffirma_hinzufügen(projekt, firma = f, rolle = r)

    # Liste Vorlagen WFSch
    li_v_wfsch = []
    for v_wfsch in V_Workflow_Schema.objects.using(DB_SUPER).all():
        if not v_wfsch.gelöscht() and not v_wfsch.instanz(projekt):
            li_v_wfsch.append(v_wfsch.v_wfsch_dict())

    # Liste WFSch
    li_wfsch = []
    for wfsch in Workflow_Schema.objects.using(db_projekt).all():
        if not wfsch.gelöscht(projekt):
            li_wfsch.append(wfsch.wfsch_dict(projekt))
    
    context = {
        'projekt_id': projekt.id,
        'liste_v_wfsch': li_v_wfsch,
        'liste_wfsch': li_wfsch,
        'kontrolle':kontrolle
        }

    return render(request, './projektadmin/übersicht_wfsch.html', context)

################################################
# Ordnerverwaltung

def übersicht_ordner_view(request, projekt_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung()

    # POST
    if request.method == 'POST':

        # EREIGNIS PJS IMPORTIEREN
        if request.POST['ereignis'] == 'pjs_importieren':
            pjs = V_Projektstruktur.objects.using(DB_SUPER).get(pk = request.POST['pjs_id'])
            pjs.in_db_anlegen(projekt)

        # EREIGNIS ORDNER LÖSCHEN
        if request.POST['ereignis'] == 'ordner_löschen':
            ordner = Ordner.objects.using(db_projekt).get(pk = request.POST['ordner_id'])
            ordner.löschen(projekt)

        # EREIGNIS ORDNER ANLEGEN
        if request.POST['ereignis'] == 'ordner_anlegen':
            neuer_ordner = Ordner.objects.using(db_projekt).create(
                zeitstempel = timezone.now()
                )
            neuer_ordner.bezeichnung_ändern(projekt, request.POST['ordner_bezeichnung'])
            neuer_ordner.entlöschen(projekt)

        # EREIGNIS UNTERORDNER ANLEGEN
        if request.POST['ereignis'] == 'unterordner_anlegen':
            ordner = Ordner.objects.using(db_projekt).get(pk = request.POST['ordner_id'])
            ordner.unterordner_anlegen(projekt, request.POST['unterordner_bezeichnung'])

        # EREIGNIS WFSCH ÄNDERN
        if request.POST['ereignis'] == 'wfsch_ändern':
            ordner = Ordner.objects.using(db_projekt).get(pk = request.POST['ordner_id'])
            if request.POST['wfsch_id'] == 'Kein WFSch':
                ordner.verbindung_wfsch_löschen(projekt)    
            else:
                wfsch = Workflow_Schema.objects.using(db_projekt).get(pk = request.POST['wfsch_id'])
                ordner.verbindung_wfsch_herstellen(projekt, wfsch)

    # Packe context und lade Template
    context = {
        'projekt_id': projekt_id,
        'liste_ordner': liste_ordner_dict(projekt),
        'liste_wfsch': liste_wfsch_dict(projekt),
        'liste_v_pjs': liste_v_pjs_dict() if not Projektstruktur.objects.using(db_projekt).all() else None # Nur ausfüllen wenn noch keine PJS importiert
        } 
    
    return render(request, './projektadmin/übersicht_ordner.html', context)

def freigabeverwaltung_ordner_view(request, firma_id, projekt_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung()
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    if request.method == 'POST':
        # EREIGNIS FREIGABEN AKTUALISIEREN
        if request.POST['ereignis'] == 'aktualisieren':
            for key, value in request.POST.items():
                if 'freigabe' in value:
                    ordner = Ordner.objects.using(db_projekt).get(pk = key)
                    if value == 'freigabe_lesen':
                        ordner.lesefreigabe_erteilen_firma(projekt, firma)
                    elif value == 'freigabe_upload':
                        ordner.uploadfreigabe_erteilen_firma(projekt, firma)
                    else:
                        ordner.freigaben_entziehen_firma(projekt, firma)

        # EREIGNIS FREIGABEN ÜBERNEHMEN ROLLE
        if request.POST['ereignis'] == 'freigaben_rollen_übernehmen':
            for o in liste_ordner(projekt):
                o.freigaben_übertragen_rollen_firma(projekt, firma)

    li_ordner_dict = []
    for o in liste_ordner(projekt):
        dict_o = o.ordner_dict(projekt, request.user)
        dict_o['freigabe_lesen'] = True if o.lesefreigabe_firma(projekt, firma) else False
        dict_o['freigabe_upload'] = True if o.uploadfreigabe_firma(projekt, firma) else False
        dict_o['keine_freigabe'] = True if not dict_o['freigabe_lesen'] and not dict_o['freigabe_upload'] else False
        li_ordner_dict.append(dict_o)
    
    # Packe Context und lade Template
    dict_firma = firma.firma_dict()
    dict_firma['liste_rollen'] = liste_rollen_firma_dict(projekt, firma)

    context = {
        'projekt_id': projekt_id,
        'firma': dict_firma,
        'liste_ordner': li_ordner_dict,
        }

    return render(request, './projektadmin/freigabeverwaltung_ordner.html', context)
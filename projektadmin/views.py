from django.http.response import FileResponse
from django.shortcuts import render
from django.core.files import File

import funktionen
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import Ordner_WFSch, Projektstruktur, V_Workflow_Schema, WFSch_Stufe_Rolle, WF_Prüferstatus, WF_Stufe_Mitarbeiter, Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Firma, Ordner, Ordner_Firma_Freigabe, Dokument, Status, Datei, Datei_Download, Pfad, liste_wf_zur_bearbeitung_dict
from .forms import FirmaNeuForm, WFSchWählenForm
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.utils import timezone

from superadmin.models import Projekt, Firma
from projektadmin.models import V_Projektstruktur, Rolle, Dokument_Download, Workflow, listendarstellung_ordnerbaum_gesamt, liste_oberste_ordner_dict, liste_rollen_dict, liste_rollen, liste_rollen_firma, liste_rollen_firma_dict, liste_ordner_dict, liste_ordner, liste_wfsch_dict, liste_v_pjs_dict, firma_projektrollen_zuweisen
from funktionen import hole_objs, hole_dicts, workflows, ordnerfunktionen
from gernotbau.settings import DB_SUPER, MEDIA_ROOT

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
    
    # POST
    if request.method == 'POST':
        neue_firma = projekt.firma_anlegen(formulardaten = request.POST, ist_projektadmin = False)
        firma_projektrollen_zuweisen(projekt, firma = neue_firma, formulardaten = request.POST)
        
        return HttpResponseRedirect(reverse('projektadmin:übersicht_firmen', args = [projekt_id]))

    # Packe Context und Lade Template
    context = {
        'liste_rollen': liste_rollen_dict(projekt),
        'projekt_id': projekt_id,
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
                for r in s._liste_rollen(projekt):
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





#                             #
##                           ##
### -----    DOKAB    ----- ### 
### -----             ----- ###
##                           ##
#                             #


#############################################################
# Ordner

def übersicht_ordnerinhalt_root_view(request, projekt_id):
    # TODO: Kontrolle Login

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)

    context = {
        'projekt': projekt,
        'liste_ordnerbaum': listendarstellung_ordnerbaum_gesamt(projekt, request.user),
        'liste_unterordner': liste_oberste_ordner_dict(projekt, request.user)
        }
    
    return render(request, './projektadmin/übersicht_ordnerinhalt.html', context)

def übersicht_ordnerinhalt_view(request, projekt_id, ordner_id):
    # TODO: Kontrolle Login
    
    # Packe context und Lade Übersicht Ordnerinhalt
    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    aktueller_ordner = Ordner.objects.using(projekt.db_bezeichnung()).get(pk = ordner_id)

    context = {
        'projekt': projekt.__dict__,
        'aktueller_ordner': aktueller_ordner.ordner_dict(projekt, request.user), 
        'liste_ordnerbaum': listendarstellung_ordnerbaum_gesamt(projekt, request.user),
        'liste_dokumente_freigegeben': aktueller_ordner._liste_dokumente_freigegeben_dict(projekt),
        'liste_dokumente_mitarbeiter': aktueller_ordner._liste_dokumente_mitarbeiter_dict(projekt, request.user),
        'liste_unterordner': aktueller_ordner._liste_unterordner_dict(projekt, request.user),
        }

    return render(request, './projektadmin/übersicht_ordnerinhalt.html', context)

def upload_dokument_view(request, projekt_id, ordner_id):
    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    ordner = Ordner.objects.using(projekt.db_bezeichnung()).get(pk = ordner_id)

    # POST
    if request.method == 'POST':
        neues_dok = ordner._dokument_anlegen(
            projekt = projekt,
            mitarbeiter = request.user,
            formulardaten = request.POST,
            liste_dateien = request.FILES.getlist('dateien'))

        # Workflow anlegen
        if ordner._wfsch(projekt):
            ordner._wfsch(projekt)._workflow_anlegen(projekt, neues_dok)
        
    # Context packen und Formular laden
    context = {
        'projekt': projekt.projekt_dict(),
        'ordner': ordner.ordner_dict(projekt, mitarbeiter = request.user),
        }
    return render(request, './projektadmin/upload_formular.html', context)

def detailansicht_dokument_view(request, projekt_id, dokument_id):
    # TODO: Kontrolle Login

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    dokument = Dokument.objects.using(projekt.db_bezeichnung()).get(pk = dokument_id)

    # POST
    if request.method == 'POST':
        
        # EREIGNIS KOMMENTAR VERFASSEN
        if request.POST['ereignis'] == 'kommentar_verfassen':
            dokument._kommentar_anlegen(projekt = projekt, mitarbeiter = request.user, kommentartext_neu = request.POST['kommentartext'])

        # EREIGNIS DOWNLOAD GESAMT
        if request.POST['ereignis'] == 'download_gesamt':
            Dokument_Download.objects.using(projekt.db_bezeichnung()).create(
                dokument = dokument, 
                mitarbeiter_id = request.user.id, 
                zeitstempel = timezone.now())

            response = HttpResponse(dokument._zip_dateien(projekt), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={dokument._bezeichnung(projekt)}.zip'

            return response

        # EREIGNIS DOWNLOAD DATEI
        if request.POST['ereignis'] == 'download_datei':
            datei = Datei.objects.using(projekt.db_bezeichnung()).get(pk = request.POST['datei_id'])
            Datei_Download.objects.using(projekt.db_bezeichnung()).create(
                datei = datei,
                mitarbeiter_id = request.user.id,
                zeitstempel = timezone.now()
                )

            projektpfad = Pfad.objects.using(projekt.db_bezeichnung()).latest('zeitstempel').pfad
            quellpfad = str(MEDIA_ROOT) + '/' + projektpfad + '/' + str(datei.id) + '_' + str(datei.dateiname)
            
            return FileResponse(open(quellpfad, 'rb'), as_attachment = True)

    # Packe context und lade Template
    dict_ordner = dokument._ordner(projekt).__dict__
    dict_ordner['bezeichnung'] = dokument._ordner(projekt).bezeichnung(projekt)
    dict_dokument = dokument._dokument_dict(projekt)
    if dokument._workflow(projekt):
        dict_dokument['wfsch'] = dokument._workflow(projekt).wfsch._bezeichnung(projekt)

    context = {
        'projekt': projekt,
        'dokument': dict_dokument,
        'ordner': dict_ordner,
        'liste_dateien': dokument._liste_dateien_dict(projekt),
        'liste_dokhist': dokument._liste_dokhist(projekt),
        }

    return render(request, './projektadmin/detailansicht_dokument.html', context)

def detailansicht_wf_view(request, projekt_id, wf_id):
    # TODO: Kontrolle Login
    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    workflow = Workflow.objects.using(projekt.db_bezeichnung()).get(pk = wf_id)
    ordner = workflow.dokument._ordner(projekt)
    dict_ordner = ordner.__dict__
    dict_ordner['bezeichnung'] = ordner.bezeichnung(projekt)

    context = {
        'workflow': workflow._workflow_dict(projekt, mitarbeiter = request.user),
        'projekt': projekt.__dict__,
        'ordner': dict_ordner
        }

    return render(request, './projektadmin/detailansicht_wf.html', context)

def wf_zur_bearbeitung_view(request, projekt_id):
    # TODO: Kontrolle Login

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)

    # POST
    if request.method == 'POST':
        status_fg = Status.objects.using(projekt.db_bezeichnung()).get_or_create(bezeichnung = 'Freigegeben')[0]
        status_ab = Status.objects.using(projekt.db_bezeichnung()).get_or_create(bezeichnung = 'Abgelehnt')[0]
        status_rf = Status.objects.using(projekt.db_bezeichnung()).get_or_create(bezeichnung = 'Rückfrage')[0]
        wf_st_ma = WF_Stufe_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get(pk = request.POST['verbindung_wf_st_ma_id'])
        workflow = Workflow.objects.using(projekt.db_bezeichnung()).get(pk = request.POST['wf_id'])

        # EREIGNIS FREIGEGEBEN:
        if request.POST['ereignis'] == 'freigegeben':
            WF_Prüferstatus.objects.using(projekt.db_bezeichnung()).create(
                wf_stufe_mitarbeiter = wf_st_ma,
                status = status_fg,
                zeitstempel = timezone.now()
                )
            workflow._auswerten(projekt)

        if request.POST['ereignis'] == 'abgelehnt':
            WF_Prüferstatus.objects.using(projekt.db_bezeichnung()).create(
                wf_stufe_mitarbeiter = wf_st_ma,
                status = status_ab,
                zeitstempel = timezone.now()
                )
            workflow._auswerten(projekt)
            # TODO: Kommentar angeben
            
        if request.POST['ereignis'] == 'rückfrage':
            WF_Prüferstatus.objects.using(projekt.db_bezeichnung()).create(
                wf_stufe_mitarbeiter = wf_st_ma,
                status = status_rf,
                zeitstempel = timezone.now()
                )
            # TODO: Rückfrage angeben

    context = {
        'projekt': projekt,
        'liste_workflows': liste_wf_zur_bearbeitung_dict(projekt, request.user)
        }

    return render(request, './projektadmin/wf_zur_bearbeitung.html', context)
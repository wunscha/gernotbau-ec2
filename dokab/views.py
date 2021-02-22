from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
import datetime

from gernotbau.settings import BASE_DIR, DB_SUPER
from projektadmin.funktionen import Ordnerbaum, sortierte_stufenliste
from projektadmin.models import Ordner_Firma_Freigabe, Ordner, Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Mitarbeiter, liste_oberste_ordner_dict, listendarstellung_ordnerbaum_gesamt
from superadmin.models import Firma, Projekt
from .funktionen import user_hat_ordnerzugriff, speichere_datei_chunks, workflow_stufe_ist_aktuell, liste_prüffirmen, aktuelle_workflow_stufe
from funktionen import dateifunktionen, hole_objs, ordnerfunktionen, hole_dicts, workflows

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
    
    return render(request, './dokab/übersicht_ordnerinhalt.html', context)

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

    return render(request, './dokab/übersicht_ordnerinhalt.html', context)

def upload_dokument_view(request, projekt_id, ordner_id):
    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    ordner = Ordner.objects.using(projekt.db_bezeichnung()).get(pk = ordner_id)

    # POST
    if request.method == 'POST':
        ordner._dokument_anlegen(
            projekt = projekt,
            mitarbeiter = request.user,
            formulardaten = request.POST,
            liste_dateien = request.FILES.getlist('dateien'))

    # Context packen und Formular laden
    context = {
        'projekt': projekt.projekt_dict(),
        'ordner': ordner.ordner_dict(projekt, mitarbeiter = request.user),
        }
    return render(request, './dokab/upload_formular.html', context)

def detailansicht_dokument_view(request, projekt_id, dokument_id):
    # TODO: Kontrolle Login

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    dokument = Dokument.objects.using(projekt.db_bezeichnung()).get(pk = dokument_id)

    # Packe context und lade Template
    context = {
        'projekt_id': projekt.id,
        'dokument': dokument._dokument_dict(projekt),
        'ordner_id': dokument._ordner(projekt).id,
        'liste_dateien': dokument._liste_dateien_dict(projekt),
        'liste_dokhist': dokument._liste_dokhist(projekt),
        }

    return render(request, './dokab/detailansicht_dokument.html', context)
    

#############################################################
# Workflows

def übersicht_wf_eigene_dok_view(request, projekt_id):

    # Kontrolle Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        projekt = Projekt.objects.using('default').get(pk = projekt_id)

        li_wf_obj = Workflow.objects.using(projekt_id).filter(dokument__mitarbeiter_id = request.user.id)
        li_wf_obj_aktuell = hole_objs.filtere_aktive_wf(projekt = projekt, liste_wf_obj = li_wf_obj)

        # Context packen und WF-Übersicht laden:
        context = {
            'liste_workflows': hole_dicts.liste_workflows(projekt = projekt, liste_wf_obj = li_wf_obj_aktuell),
            'projekt': projekt.__dict__
            }
        return render(request, './dokab/übersicht_wf_eigene_dok.html', context)

def übersicht_wf_zur_bearbeitung_view(request, projekt_id):

    # Kontrolle Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        projekt = Projekt.objects.using('default').get(pk = projekt_id)
        fehlermeldung = '' # Vorbereitung für Context

        # Wenn POST: 
        # - Status ändern und Workflowstatus updaten
        # - ggf Weiterleitung zu Rückfrageformular
        if request.method == 'POST':
            wf_stufe = Workflow_Stufe.objects.using(projekt_id).get(pk = request.POST['wf_stufe_id'])
            
            # Neuer Eintrag MA_Stufe_Status_Update_Status
            eintrag_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(projekt_id).get(
                mitarbeiter_id = request.user.id, 
                workflow_stufe = wf_stufe
                )
            neuer_eintrag_ma_status = MA_Stufe_Status_Update_Status(
                ma_stufe_status = eintrag_ma_stufe_status,
                status = workflows.status(projekt = projekt, statusbezeichnung = request.POST['status']),
                zeitstempel = timezone.now(),
                )
            # --> Speichern erst nachdem Statuskommentar geprüft wurde

            # Statuskommentar prüfen und Anlegen
            statusbezeichnung = request.POST['status']
            if not request.POST['text_statuskommentar']:
                # Kommentar bei Status 'Abgelehnt' und 'Rückfrage' erforderlich
                if statusbezeichnung in ['Abgelehnt', 'Rückfrage']:
                    fehlermeldung = 'Bitte füllen Sie das Kommentarfeld aus'
                else: neuer_eintrag_ma_status.save(using = projekt_id)
            else:
                neuer_eintrag_ma_status.save(using = projekt_id)
                # Neues Statuskommentar anlegen
                neues_statuskommentar = Statuskommentar(
                    ma_stufe_status_update_status = neuer_eintrag_ma_status,
                    text = request.POST['text_statuskommentar']
                    )
                neues_statuskommentar.save(using = projekt_id)
            
        
            # TODO: Weiterleitung zu Rückfrageformular, wenn request.POST['status'] == 'Rückfrage'
            # TODO: InfoMails

            workflows.aktualisiere_wf(projekt = projekt, workflow = wf_stufe.workflow)

        # Context packen und WF-Übersicht laden:
        li_wf_obj = hole_objs.liste_wf_zur_bearbeitung(request, projekt = projekt)
        platzhalter_kommentar_status = 'Kommentar für Status "Abgelehnt" oder "Rückfrage" erforderlich. (Kommentar für Status "Freigabe" ist optional)'
        
        context = {
            'liste_workflows': hole_dicts.liste_workflows(projekt = projekt, liste_wf_obj = li_wf_obj),
            'projekt': projekt.__dict__,
            'platzhalter_kommentar_status': platzhalter_kommentar_status,
            'fehlermeldung': fehlermeldung
        }
        return render(request, './dokab/übersicht_wf_zur_bearbeitung.html', context)

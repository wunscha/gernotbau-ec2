from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
import datetime

from gernotbau.settings import BASE_DIR
from projektadmin.funktionen import Ordnerbaum, sortierte_stufenliste
from projektadmin.models import Ordner_Firma_Freigabe, Ordner, Workflow_Schema, Workflow_Schema_Stufe, WFSch_Stufe_Mitarbeiter
from superadmin.models import Firma, Projekt
from .models import Dokument, Paket, Status, Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status, Dokumentenhistorie_Eintrag, Anhang, Ereignis
from .funktionen import user_hat_ordnerzugriff, speichere_datei_chunks, workflow_stufe_ist_aktuell

#############################################################
# Ordner

def weiterleitung_root(request, projekt_id):
# Leite weiter zur Anzeige Root-Ordner
    projekt = Projekt.objects.get(pk = projekt_id)
    root_ordner = Ordner.objects.get(projekt = projekt, ist_root_ordner = True)

    return HttpResponseRedirect(reverse('dokab:ordner_inhalt', args = [projekt_id, root_ordner.id]))

def ordner_inhalt(request, projekt_id, ordner_id):
# Zeige Ordnerinhalt, wenn User eingeloggt und Ordnerzugriff
    
    if request.user.is_authenticated:
        # -------ORDNERBAUM----------

        # Erstelle dict für Anzeige Ordnerbaum:
        # Hole Ordnerstruktur
        projekt = Projekt.objects.get(pk = projekt_id)
        liste_ordner = Ordner.objects.filter(projekt = projekt)
        ordner_root = Ordner.objects.get(projekt = projekt, ist_root_ordner = True)
        # Erstelle Instanz von Ordnerbaum und befülle dict_ordnerbaum für context
        ordnerbaum_instanz = Ordnerbaum()
        dict_ordnerbaum = ordnerbaum_instanz.erstelle_dict_ordnerbaum(liste_ordner, ordner_root)
        # Hole Ordnerfreigaben für die Firma
        firma = request.user.firma
        ordnerbaum = []
        for key, value in dict_ordnerbaum.items():
            # Hole Eintrag in Ordner_Firma_Freigabe, wenn vorhanden, sonst erstelle Neuen Eintrag
            '''
            # TODO: 
            # Vorteil --> Es muüssen nicht alle Freigabe-Einträge neu erstellt wenn neuer Ordner od. Firma angelegt wird; 
            # Nachteil --> Evtl. Erzeugung von doppelten Einträgen möglich, oder Freigabe werden überschrieben?
            '''
            ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get_or_create(
                firma = firma, 
                ordner = value, 
                defaults = {
                    'projekt':projekt, 
                    'freigabe_lesen':False, 
                    'freigabe_upload':False
                    }
                )
            
            # Dict Einzelordner befüllen
            dict_einzelordner = {}
            dict_einzelordner['ordner_darstellung'] = key
            dict_einzelordner['ordner'] = value
            dict_einzelordner['ordner_freigabe_lesen'] = ordner_firma_freigabe[0].freigabe_lesen # Index erforderlich wegen 'get_or_create'
            dict_einzelordner['ordner_freigabe_upload'] = ordner_firma_freigabe[0].freigabe_upload # Index erforderlich wegen 'get_or_create'

            # Ordnerbaum befüllen
            ordnerbaum.append(dict_einzelordner)

        
        # Packe Context für Ordnerbaum
        ordner = Ordner.objects.get(pk = ordner_id)
        context = {
            'projekt_id':projekt_id,
            'ordner_id':ordner_id,
            'ordner':ordner,
            'ordnerbaum':ordnerbaum
        }

        if user_hat_ordnerzugriff(user = request.user, ordner_id = ordner_id, projekt_id = projekt_id):
        # ----------- DOKUMENTE -------------
            ordner = Ordner.objects.get(pk = ordner_id)
            liste_unterordner = Ordner.objects.filter(überordner = ordner)
            liste_dokumente = Dokument.objects.filter(ordner = ordner)
            
            # Füge zu Context Ordnerinhalt zu Context hinzu
            context['liste_unterordner'] = liste_unterordner
            context['liste_dokumente'] = liste_dokumente

            # Füge Uploadberechtigung zu Context hinzu
            ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get(firma = firma, ordner = ordner)
            context['freigabe_upload'] = ordner_firma_freigabe.freigabe_upload

            return render(request, 'ordner_inhalt.html', context)
        
        else:
            return render(request, 'dokab_ordner_zugriff_verweigert.html', context)

#############################################################
# Konstanten für Stati (Indizes wegen 'get_or_create')
STATI = {}
STATI['in_bearbeitung'] = Status.objects.get_or_create(bezeichnung = 'In Bearbeitung')[0]
STATI['warten_auf_vorstufe'] = Status.objects.get_or_create(bezeichnung = 'Warten auf Vorstufe')[0]
STATI['rückfrage'] = Status.objects.get_or_create(bezeichnung = 'Rückfrage')[0]
STATI['abgelehnt'] = Status.objects.get_or_create(bezeichnung = 'Abgelehnt')[0]
STATI['freigegeben'] = Status.objects.get_or_create(bezeichnung = 'Freigegeben')[0]

# Konstanten für Ereignisse (Indizes wegen 'get_or_create')
EREIGNISSE = {}
EREIGNISSE['upload'] = Ereignis.objects.get_or_create(bezeichnung = 'Upload')[0]
EREIGNISSE['workflow_eröffnet'] = Ereignis.objects.get_or_create(bezeichnung = 'Workflow Eröffnet')[0]

#############################################################
# Dokumente

def upload(request, projekt_id, ordner_id):
    
# Wenn user keinen Uploadzugriff hat: Zugriff verweigert
# Wenn POST: Führe Upload durch
# Wenn nicht POST: Zeige Upload Formular
    ordner = Ordner.objects.get(pk = ordner_id)
    firma = request.user.firma
    ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get(ordner = ordner, firma = firma)
    if ordner_firma_freigabe.freigabe_upload:

        if request.method == 'POST':
            datei = request.FILES['datei']
            
            # Lege Paket und Dokument in DB an
            paket_bezeichnung = request.POST['paket']
            paket = Paket.objects.create(bezeichnung = paket_bezeichnung)
            zielpfad = str(BASE_DIR) + '/_DATEIABLAGE/' #TODO: Verwaltung Ablagepfad anpassen

            neues_dokument = Dokument.objects.create(
                bezeichnung = datei.name,
                pfad = zielpfad + datei.name,
                zeitstempel = timezone.now(),
                mitarbeiter = request.user,
                paket = paket,
                ordner = ordner
            )

            # Lege DokHist Eintrag an
            text = 'Dokument {neues_dokumen.bezeichnung} wurde hochgeladen'
            Dokumentenhistorie_Eintrag.objects.create(
                zeitstempel = timezone.now(),
                mitarbeiter = request.user,
                dokument = neues_dokument,
                text = text, 
                ereignis = EREIGNISSE['upload']
            )

            # Datei hochladen
            speichere_datei_chunks(datei, zielpfad)

            # -------- WORKFLOW ANLEGEN ---------
            # Lege neuen Workflow an, wenn Workflow-Schema vorhanden
            workflow_schema = ordner.workflow_schema
            if workflow_schema:
                workflow = Workflow.objects.create(
                    dokument = neues_dokument,
                    workflow_schema = workflow_schema,
                    status = STATI['in_bearbeitung'],
                    abgeschlossen = False
                )
                text = 'Workflow {workflow_schema.bezeichnung} für Dokument {neues_dokument.bezeichnung} wurde eröffnet'
                Dokumentenhistorie_Eintrag.objects.create(
                    zeitstempel = timezone.now(),
                    mitarbeiter = request.user,
                    dokument = neues_dokument,
                    text = text, 
                    ereignis = EREIGNISSE['workflow_eröffnet']
                )

                # Lege Workflow-Stufen an
                liste_wfsch_stufen = Workflow_Schema_Stufe.objects.filter(workflow_schema = workflow_schema)
                liste_wfsch_stufen = sortierte_stufenliste(liste_wfsch_stufen)
                aktuelle_stufe = None
                for wfsch_stufe in liste_wfsch_stufen:
                    # Erzeuge Stufe
                    vorstufe = aktuelle_stufe
                    aktuelle_wfsch_stufe = wfsch_stufe
                    aktuelle_stufe = Workflow_Stufe(workflow = workflow, vorstufe = vorstufe)
                    aktuelle_stufe.save()
                    
                    # Lege MA_Stufe_Stati an
                    liste_wfsch_stufe_ma = WFSch_Stufe_Mitarbeiter.objects.filter(wfsch_stufe = aktuelle_wfsch_stufe)
                    for wfsch_stufe_ma in liste_wfsch_stufe_ma:
                        if vorstufe:
                            status = STATI['warten_auf_vorstufe']
                        else:
                            status = STATI['in_bearbeitung']
                        Mitarbeiter_Stufe_Status.objects.create(
                                mitarbeiter = wfsch_stufe_ma.mitarbeiter, 
                                status = status,
                                workflow_stufe = aktuelle_stufe,
                                immer_erforderlich = wfsch_stufe_ma.immer_erforderlich
                                )

            # TODO: InfoMails

            return HttpResponseRedirect(reverse('dokab:ordner_inhalt',args=[projekt_id, ordner_id]))

        else:
        # Wenn nicht POST:
        # --> Zeige Upload-Formular für Ordner
            context = {
                'ordner':ordner,
                'ordner_id':ordner_id,
                'projekt_id':projekt_id
                }

            return render(request, 'upload.html', context)

#############################################################
# Workflows

def workflows_übersicht(request, projekt_id):
# Hole alle Workflows für Dokumente des Users und für der User Prüfer ist
# und Leite zu Workflow-Übersicht weiter

    # Hole Workflows für die Dokumente des Users
    liste_workflows_userdok = Workflow.objects.filter(dokument__mitarbeiter = request.user)
    
    # Hole Workflows, für die Prüfung durch User ausständig ist (Wenn Stufe aktuell, für die User Prüfer)
    liste_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.filter(mitarbeiter = request.user)
    liste_workflows_userprüfer = []
    
    for ma_stufe_status in liste_ma_stufe_status:
        workflow_stufe = ma_stufe_status.workflow_stufe
        workflow = workflow_stufe.workflow

        if workflow_stufe_ist_aktuell(workflow_stufe):
            liste_workflows_userprüfer.append(workflow)

    # Fülle Context und Rendere Workflow-Übersicht
    context = {
        'projekt_id':projekt_id,
        'liste_workflows_userdok':liste_workflows_userdok,
        'liste_workflows_userprüfer':liste_workflows_userprüfer
    }

    return render(request, 'dokab_workflows_übersicht.html', context)

    # Rendere "dokab_workflows_übersicht.html"

def aktualisiere_workflow(request, projekt_id):
    pass
    # Wenn Status == Abgelehnt:
    # --> WF-Stufe = inaktiv
    # --> WF-Status = Abgelehnt
    # --> WF = abgeschlossen
    # --> DokHist-Eintrag
    # --> InfoMail
    # --> Weiterleitung zu WF-Übersicht

    # Wenn Status == Rückfrage:
    # --> Prüfer-Status = Rückfrage
    # --> DokHist-Eintrag
    # --> InfoMail
    # --> Weiterleitung zu WF-Übersicht

    # Wenn Status == Freigegeben:
    # --> Prüfer-Status = Freigegeben
    # --> DokHist-Eintrag
    # --> Prüfe für jede Prüffirma ob Status Prüffirma == Freigegeben (Min. eine Freigabe und alle Freigaben von erforderlichen Prüfern):
    #
    # --> Wenn Status aller Prüffirmen in der Stufe == Freigegeben:
    #    --> Stufe = abgeschlossen
    #    --> DokHist-Eintrag
    #
    #    --> Wenn nächste Stufe vorhanden:
    #        --> Status nächste Stufe = In Bearbeitung
    #        --> Für jeden Prüfer in Stufe Status = In Bearbeitung
    #        --> DokHist-Eintrag
    #        --> InfoMails
    #        --> Weiterleitung zu WF-Übersicht
    #   
    #    --> Sonst:
    #        --> WF-Status = Freigegeben
    #        --> WF = abgeschlossen
    #        --> DokHist-Eintrag
    #        --> InfoMails
    #        --> Weiterleitung zu WF-Übersicht

    # Wenn Status == Rückfrage:
    # --> Prüfer-Status = Rückfrage
    # --> WF-Status = Rückfrage
    # --> DokHist-Eintrag
    # --> InfoMails
    # --> Weiterleitung zu WF-Übersicht
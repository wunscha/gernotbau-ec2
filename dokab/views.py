from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
import datetime

from gernotbau.settings import BASE_DIR
from projektadmin.funktionen import Ordnerbaum, sortierte_stufenliste
from projektadmin.models import Ordner_Firma_Freigabe, Ordner, Workflow_Schema, Workflow_Schema_Stufe, WFSch_Stufe_Mitarbeiter
from superadmin.models import Firma, Projekt
from .models import Dokument, Status, Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status, Dokumentenhistorie_Eintrag, Anhang, Ereignis, Datei
from .funktionen import user_hat_ordnerzugriff, speichere_datei_chunks, workflow_stufe_ist_aktuell, liste_prüffirmen, aktuelle_workflow_stufe
from funktionen import dateifunktionen, ordnerfunktionen, hole_dicts, workflows

#############################################################
# Ordner

def übersicht_ordnerinhalt_root_view(request, projekt_id):
# Leite weiter zur Übersicht Ordnerinhalt Root-Ordner
    rootordner = Ordner.objects.using(projekt_id).get(ist_root_ordner = True)
    return HttpResponseRedirect(reverse('dokab:übersicht_ordnerinhalt', args=(projekt_id, rootordner.id)))

def übersicht_ordnerinhalt_view(request, projekt_id, ordner_id):
    # Kontrolle Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        # Packe context und Lade Übersicht Ordnerinhalt
        projekt = Projekt.objects.using('default').get(pk = projekt_id)
        aktueller_ordner = Ordner.objects.using(projekt_id).get(pk = ordner_id)

        # Kontrolle Ordnerzugriff (Weiterverwendung 'zugriff_verweigert' im context):
        if not ordnerfunktionen.userfirma_hat_ordnerzugriff(request.user, ordner_id, projekt_id):
            zugriff_verweigert = True
            # TODO: Anzeige Fehlermeldung beim Laden von 'übersicht_ordnerinhalt.html"
            context = {
                'projekt':projekt.__dict__,
                'ordner':aktueller_ordner.__dict__,
                'zugriff_verweigert': zugriff_verweigert
                }
            return render(request, './dokab/übersicht_ordnerinhalt.html', context)

        else:
            zugriff_verweigert = False
            
            # POST: Download oder ähnliches
            if request.method == 'POST':
                pass

            dict_aktueller_ordner = hole_dicts.ordner_mit_freigaben(
                projekt = projekt, 
                firma = request.user.firma,
                ordner = aktueller_ordner
                )
            
            liste_ordnerbaum = ordnerfunktionen.erzeuge_darstellung_ordnerbaum(
                projekt = projekt, 
                root_ordner = Ordner.objects.using(projekt_id).get(ist_root_ordner = True),
                firma = request.user.firma
            )
            
            liste_dokumente = hole_dicts.liste_dokumente_ordner(
                projekt = projekt, 
                ordner = aktueller_ordner
                )
            
            liste_uo = hole_dicts.liste_unterordner(
                projekt = projekt,
                firma = request.user.firma,
                ordner = aktueller_ordner
            )

            context = {
                'projekt': projekt.__dict__,
                'aktueller_ordner': dict_aktueller_ordner, 
                'liste_ordnerbaum': liste_ordnerbaum,
                'liste_dokumente': liste_dokumente,
                'liste_unterordner': liste_uo,
                'zugriff_verweigert': zugriff_verweigert,
            }

            return render(request, './dokab/übersicht_ordnerinhalt.html', context)

def upload(request, projekt_id, ordner_id):
    # Kontrolle Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        # Kontrolle Uploadfreigabe (Weiterverwendung 'zugriff_verweigert' im context):
        if not ordnerfunktionen.userfirma_hat_uploadfreigabe(request.user, ordner_id, projekt_id):
            zugriff_verweigert = True
            # TODO: Anzeige Fehlermeldung beim Laden von 'übersicht_ordnerinhalt.html"
        
        else:
            projekt = Projekt.objects.using('default').get(pk = projekt_id)
            ordner = Ordner.objects.using(projekt_id).get(pk = ordner_id)
            
            # POST Upload durchführen und Workflow initiieren
            if request.method == 'POST':
                
                # Lege Paket und Dokument in DB an
                dokument_bezeichnung = request.POST['dokument_bezeichnung']
                zielpfad = str(BASE_DIR) + '/_DATEIABLAGE/' #TODO: Verwaltung Ablagepfad anpassen

                neues_dokument = Dokument(
                    bezeichnung = dokument_bezeichnung,
                    pfad = zielpfad,
                    zeitstempel = timezone.now(),
                    mitarbeiter_id = request.user.id,
                    ordner = Ordner.objects.using(projekt_id).get(pk = ordner_id)
                    )
                neues_dokument.save(using = projekt_id)

                # DokHist-Eintrag Erstellung Dokument
                dokhist_eintrag_neu = Dokumentenhistorie_Eintrag(
                    text = 'Neues Dokument angelegt: ' + neues_dokument.bezeichnung,
                    zeitstempel = timezone.now(),
                    dokument = neues_dokument,
                    ereignis = Ereignis.objects.using(projekt_id).get(bezeichnung = 'Upload'),
                )
                dokhist_eintrag_neu.save(using = projekt_id)

                # Dateien in DB anlegen und hochladen
                for datei in request.FILES:
                    neue_datei = Datei(
                        dateiname = datei,
                        dokument = neues_dokument,
                        pfad = neues_dokument.pfad + datei
                    )
                    neue_datei.save(using = projekt_id)

                    dateifunktionen.speichere_datei_chunks(request.FILES.get(datei), zielpfad)

                    # DokHist-Eintrag Upload Datei
                    dokhist_eintrag_neu = Dokumentenhistorie_Eintrag(
                    text = 'Datei hochgeladen: ' + neue_datei.dateiname,
                    zeitstempel = timezone.now(),
                    dokument = neues_dokument,
                    ereignis = Ereignis.objects.using(projekt_id).get(bezeichnung = 'Upload'),
                    )
                
                # Workflow anlegen
                workflows.neuer_workflow(projekt = projekt, dokument = neues_dokument)

            # Context packen und Formular laden
            context = {
                'projekt': projekt.__dict__,
                'ordner': ordner.__dict__,
            }
            return render(request, './dokab/upload_formular.html', context)

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

def workflow_detailansicht(request, projekt_id, workflow_id):
# Zeige Workflow an, Dropdown für Änderung Status, wenn user == Prüfer

    workflow = Workflow.objects.get(pk = workflow_id)
    # liste_wf_stufen_firmen enthält eine Liste mit dicts f. jede Stufe: KEY = Firmenbezeichnung, VALUE = Liste der Prüfer
    iterierungsliste_workflow_stufen = Workflow_Stufe.objects.filter(workflow = workflow) # Liste dient nur zum Iterieren
    
    liste_wf_stufen = []
    
    # Erzeuge für jede Stufe Listeneintrag
    for workflow_stufe in iterierungsliste_workflow_stufen:

        # Erzeuge dict für jede Prüffirma in der Stufe: KEY = prüffirma.bezeichnung, VALUE = Liste MA_Stufe_Status
        dict_prüffirmen_stufe = {}
        iterierungsliste_prüffirmen = liste_prüffirmen(workflow_stufe) # Liste dient nur zum iterieren
        for prüffirma in iterierungsliste_prüffirmen:
            # Hole alle Prüfer der Prüffirma für die Stufe
            liste_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.filter(mitarbeiter__firma = prüffirma, workflow_stufe = workflow_stufe)
            
            dict_prüffirmen_stufe[prüffirma.bezeichnung] = liste_ma_stufe_status
        
        liste_wf_stufen.append(dict_prüffirmen_stufe)

    # Suche aktuelle Stufe
    aktuelle_stufe = aktuelle_workflow_stufe(workflow)
    
    # Fülle Context und Rendere Workflow-Detailansicht
    context = {
        'projekt_id':projekt_id,
        'workflow':workflow,
        'liste_wf_stufen':liste_wf_stufen,
        'aktuelle_stufe':aktuelle_stufe
    }

    return render(request, 'dokab_workflow_detailansicht.html', context)

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
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
import datetime

from gernotbau.settings import BASE_DIR
from projektadmin.funktionen import Ordnerbaum, sortierte_stufenliste
from projektadmin.models import Ordner_Firma_Freigabe, Ordner, Workflow_Schema, Workflow_Schema_Stufe, WFSch_Stufe_Mitarbeiter
from superadmin.models import Firma, Projekt
from .models import Dokument, Firma_Stufe, Status, Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status, Dokumentenhistorie_Eintrag, Anhang, Ereignis, Datei
from .funktionen import user_hat_ordnerzugriff, speichere_datei_chunks, workflow_stufe_ist_aktuell, liste_prüffirmen, aktuelle_workflow_stufe
from funktionen import dateifunktionen, hole_objs, ordnerfunktionen, hole_dicts, workflows

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

def übersicht_wf_eigene_dok_view(request, projekt_id):

    # Kontrolle Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        projekt = Projekt.objects.using('default').get(pk = projekt_id)

        qs_wf = Workflow.objects.using(projekt_id).filter(dokument__mitarbeiter_id = request.user.id)
        
        liste_workflows = []
        for wf in qs_wf:
            # Liste Workflowstufen
            qs_wf_stufen = Workflow_Stufe.objects.using(projekt_id).filter(workflow = wf)

            liste_wf_stufen = []
            for s in qs_wf_stufen:
                qs_einträge_firma_stufe = Firma_Stufe.objects.using(projekt_id).filter(workflow_stufe = s)
                
                # Liste Prüffirmen inkl. Firmenstati
                liste_prüffirmen = []
                for e in qs_einträge_firma_stufe:
                    pf = Firma.objects.using('default').get(pk = e.firma_id)
                    dict_prüffirma = pf.__dict__

                    status_pf = workflows.firmenstatus(
                        projekt = projekt, 
                        wf_stufe = s,
                        prüffirma = pf
                    )
                    dict_prüffirma['firmenstatus'] = status_pf.__dict__

                    liste_prüffirmen.append(dict_prüffirma)
                    
                # Dict wf_stufe packen und an liste_wf_stufen anhängen
                dict_wf_stufe = s.__dict__
                
                dict_wf_stufe['liste_prüffirmen'] = liste_prüffirmen
                
                status_stufe = workflows.stufenstatus(projekt = projekt, wf_stufe = s)
                dict_wf_stufe['stufenstatus'] = status_stufe.__dict__

                liste_wf_stufen.append(dict_wf_stufe)

            # Dict worfklow packen und an liste_worfklows ahnhängen
            dict_workflow = wf.__dict__
            dict_workflow['workflowschema'] = wf.workflow_schema.__dict__
            dict_workflow['dokument'] = wf.dokument.__dict__
            dict_workflow['status'] = wf.status.__dict__
            dict_workflow['liste_wf_stufen'] = liste_wf_stufen

            liste_workflows.append(dict_workflow)

        # Context packen und WF-Übersicht laden:
        context = {
            'liste_workflows': liste_workflows,
            'projekt': projekt.__dict__
        }
        return render(request, './dokab/übersicht_wf_eigene_dok.html', context)

def übersicht_wf_zur_bearbeitung_view(request, projekt_id):

    # Kontrolle Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        projekt = Projekt.objects.using('default').get(pk = projekt_id)
        
        # Wenn POST: 
        # - Status ändern und Workflowstatus updaten
        # - ggf Weiterleitung zu Rückfrageformular
        if request.method == 'POST':
            wf_stufe = Workflow_Stufe.objects.using(projekt_id).get(pk = request.POST['wf_stufe_id'])
            
            # Bisheriger Status ist nicht mehr aktuell
            alter_eintrag_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(projekt_id).get(
                mitarbeiter_id = request.user.id, 
                workflow_stufe = wf_stufe, 
                gelöscht = False
                )
            alter_eintrag_ma_stufe_status.gelöscht = True
            alter_eintrag_ma_stufe_status.save(using = projekt_id)

            # Neuen Eintrag für Status anlegen
            neuer_eintrag_ma_stufe_status = Mitarbeiter_Stufe_Status(
                status = workflows.status(projekt = projekt, statusbezeichnung = request.POST['status']),
                mitarbeiter_id = request.user.id,
                workflow_stufe = wf_stufe,
                immer_erforderlich = alter_eintrag_ma_stufe_status.immer_erforderlich,
                zeitstempel = timezone.now(),
                gelöscht = False,
                )
            neuer_eintrag_ma_stufe_status.save(using = projekt_id)

            # TODO: Weiterleitung zu Rückfrageformular, wenn request.POST['status'] == 'Rückfrage'
            # TODO: InfoMails

            workflows.aktualisiere_wf_status(projekt = projekt, workflow = wf_stufe.workflow)

        li_wf_obj = hole_objs.liste_wf_zur_bearbeitung(request, projekt = projekt)
        
        # Context packen und WF-Übersicht laden:
        context = {
            'liste_workflows': hole_dicts.liste_workflows(projekt = projekt, liste_wf_obj = li_wf_obj),
            'projekt': projekt.__dict__
        }
        return render(request, './dokab/übersicht_wf_zur_bearbeitung.html', context)

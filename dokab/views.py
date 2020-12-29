from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from projektadmin.funktionen import Ordnerbaum
from projektadmin.models import Ordner_Firma_Freigabe, Ordner
from superadmin.models import Firma, Projekt
from .models import Dokument
from .funktionen import user_hat_ordnerzugriff

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
        context = {
            'projekt_id':projekt_id,
            'ordner_id':ordner_id,
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
            pass
        # Wenn POST:
        # --> Führe Dateiupload durch
        # --> Lege Dokument in DB an
        # --> Erzeuge DokHist-Eintrag
        # --> InfoMails

        else:
        # Wenn nicht POST:
        # --> Zeige Upload-Formular für Ordner
            context = {'ordner':ordner}
            return render(request, 'upload.html', context)

#############################################################
# Workflows

def workflows_übersicht(request, projekt_id):
    pass
    # Hole Workflows für Dokumente des Users
    # Ermittle für jeden Workflow die aktive Stufe (die erste, die nicht abgeschlossen ist)

    # Hole Workflows für die der User Prüfer ist
    # Ermittle für jeden Workflow die aktive Stufe (die erste, die nicht abgeschlossen ist)
    
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
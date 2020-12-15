from django.shortcuts import render
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe
from .models import Workflow_Schema, Workflow_Schema_Stufe
from .forms import FirmaNeuForm
from superadmin.models import Projekt, Firma, Projekt_Firma_Mail
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms

################################################
# View für Workflows

# Erzeuge Strukturierte Listenansicht für die Workflowschemata
def workflowschemataView(request, projekt_id):
    projekt = Projekt.objects.get(pk = projekt_id)
    
    if user_ist_projektadmin(user = request.user, projekt_id = projekt_id):
        liste_workflowschemata = Workflow_Schema.objects.filter(projekt = projekt)
        dict_workflowschemata = {}
        liste_workflowschemata_id =[]
        
        # Dict für Workfloschemata und -stufen befüllen
        for wfsch in liste_workflowschemata:
            liste_wfsch_stufen = Workflow_Schema_Stufe.objects.filter(workflow_schema = wfsch)
            liste_wfsch_stufen = sortierte_stufenliste(liste_wfsch_stufen)
            # Dict für Workfloschemata und -stufen befüllen
            dict_workflowschemata[wfsch.bezeichnung] = liste_wfsch_stufen
            # Liste mit Worklfowschemata-IDs befüllen --> wird gebraucht für die verstecken Forms
            # für das Hinzufügen von WFSch-Stufen
            liste_workflowschemata_id.append(wfsch.id)

        # Formular für Auswahl Prüffirmen (Auswahlmöglichkeiten: Nur Firmen, die mit Projekt verbunden)
        prüffirma_neu_form = FirmaNeuForm()
        prüffirma_neu_form.fields['firma'].queryset = projekt.firma
        
        # Context für Template-Rendering zusammenstellen
        context = {
            'dict_workflowschemata':dict_workflowschemata,
            'liste_workflowschemata_id':liste_workflowschemata_id,
            'prüffirma_neu_form':prüffirma_neu_form,
            'projekt_id':projekt_id
        }

        return render(request, 'workflowschemata.html', context)
    else:
        return render(request, 'projektadmin_zugriff_verweigert.html')

def workflowschemaNeuView(request):
    # Wenn Post-Anfrage, dann wird neues Workflowschema angelegt 
    # (wenn keine Post-Anfrage, dann passiert nichts)
    if request.method == 'POST':
        projekt = Projekt.objects.get(pk = request.POST['projekt_id'])
        neues_workflowschema = Workflow_Schema.objects.create(
            bezeichnung = request.POST['bezeichnung'],
            projekt = projekt
        )

        # Weiterleitung zur Workflowschema-Übersicht
        return HttpResponseRedirect(reverse('workflowschemata', args=[request.POST['projekt_id']]))

def wfschStufeNeuView(request):
    # Wenn Post-Anfrage, dann wird neue Workflowschemastufe für das entsprechende Workflowschema angelegt 
    # (WFSch-ID ist in der POST-Anfrage enthalten).
    # Wenn keine Post-Anfrage, dann passiert nichts
    if request.method == 'POST':
        # Hole Attribute für neue Workflow-Schema-Stufe
        workflow_schema = Workflow_Schema.objects.get(pk = request.POST['wfsch_id'])
        liste_wfsch_stufen = Workflow_Schema_Stufe.objects.filter(workflow_schema = workflow_schema)
        letzte_wfsch_stufe = suche_letzte_stufe(liste_wfsch_stufen)
        projekt = Projekt.objects.get(pk=request.POST['projekt_id'])
        # Wenn schon Stufen vorhanden, dann erzeuge Workflow-Schema-Stufe mit letzter Stufe als Vorstufe
        if liste_wfsch_stufen:
            Workflow_Schema_Stufe.objects.create(
                projekt = projekt,
                workflow_schema = workflow_schema,
                vorstufe = letzte_wfsch_stufe
            )
        # Sonst erzeuge Workflow-Schema-Stufe ohne Vorstufe
        else:
            Workflow_Schema_Stufe.objects.create(
                projekt = projekt,
                workflow_schema = workflow_schema
            )

        # Weiterleitung zur Workflowschema-Übersicht
        return HttpResponseRedirect(reverse('workflowschemata', args=[request.POST['projekt_id']]))
        
    else:
        return HttpResponseRedirect(reverse('home'))

def prüffirmaHinzufügenView(request):
    # Wenn Post-Anfrage, dann wird neue Prüffirma zu WFSch-Stufe hinzugefügt.
    # Wenn keine POST-Anfrage ,dann passiert nichts.
    if request.method == 'POST':
        # Formulardaten holen
        prüffirma_daten = FirmaNeuForm(request.POST)

        if prüffirma_daten.is_valid():
            wfsch_stufe = Workflow_Schema_Stufe.objects.get(pk = request.POST['wfsch_stufe_id'])
            prüffirma = prüffirma_daten.cleaned_data['firma']
            wfsch_stufe.prüffirma.add(prüffirma)# Firma als Prüffirma hinzufügen

            #TODO: InfoMail an Prüffirma

        return HttpResponseRedirect(reverse('workflowschemata', args=[request.POST['projekt_id']]))
    else:
        return HttpResponseRedirect(reverse('home'))

################################################
# View für Firmenverwaltung

def firmenÜbersichtView(request, projekt_id):
# Zeige Auflistung der Firmen, die mit dem Projekt verbunden sind.
# Klick auf Firmennamen leitet zur Detailansicht der Firma weiter

# Prüfung Projektadmin
    if user_ist_projektadmin(request.user, projekt_id):
        projekt = Projekt.objects.get(pk = projekt_id)
        # Hole Einträge aus PJ-Fa-Througtabelle für das aktuelle Projekt
        liste_pj_fa_mail = Projekt_Firma_Mail.objects.filter(projekt = projekt)
        # Formular für Firmenauswahl vorbereiten (Auswahlmöglichkeiten: Firmen, die noch nicht bei Projekt)
        alle_firmen = Firma.objects.all()
        firmen_im_projekt = projekt.firma.all()
        firmen_außerhalb_projekt = alle_firmen.difference(firmen_im_projekt)
        firma_hinzufügen_form = FirmaNeuForm()
        firma_hinzufügen_form.fields['firma'].queryset = firmen_außerhalb_projekt
        # Packe Context und Leite Weiter auf Firmenübersicht
        context = {
            'liste_pj_fa_mail':liste_pj_fa_mail,
            'firma_hinzufügen_form':firma_hinzufügen_form,
            'projekt_id':projekt_id
        }
        return render(request, 'firmen_übersicht.html', context)

    # Wenn nicht Projektadmin Weiterleitung auf Zugriff-Vereweigert-Seite
    else:
        return render(request, 'projektadmin_zugriff_verweigert.html')

def firmaHinzufügenView(request):
# Wenn POST-Anfrage, dann füge ausgewählte Firma zum Projekt hinzu
# Wenn keine POST-Anfrage, dann passiert nichts

    if request.method == 'POST':
        # Hole Daten aus Formular und validiere
        firma_hinzufügen_daten = FirmaNeuForm(request.POST)
        if firma_hinzufügen_daten.is_valid():
            # Bereite Daten vor
            projekt = Projekt.objects.get(pk = request.POST['projekt_id'])
            firma = firma_hinzufügen_daten.cleaned_data['firma']
            email = str('%s.%s' % (projekt.kurzbezeichnung, firma.email))
            # Lege Eintrag in Through-Tabelle Projekt_Firma_Mail an
            neu_pj_fa_mail = Projekt_Firma_Mail.objects.create(
                email = email,
                firma = firma,
                ist_projektadmin = False,
                projekt = projekt
            )

            #TODO: InfoMail an Firma

        # Weiterleigung zur Projektfirmen-Übersicht
        return HttpResponseRedirect(reverse('firmen_übersicht', args=[request.POST['projekt_id']]))
    else:
        return HttpResponseRedirect(reverse('home'))
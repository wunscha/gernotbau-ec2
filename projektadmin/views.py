from django.shortcuts import render
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import Workflow_Schema, Workflow_Schema_Stufe, Ordner, Ordner_Firma_Freigabe
from .forms import FirmaNeuForm, WFSchWählenForm
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

        return HttpResponseRedirect(reverse('projektadmin:workflowschemata', args=[request.POST['projekt_id']]))
    else:
        return HttpResponseRedirect(reverse('home'))

################################################
# Views für Firmenverwaltung

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

def firmaDetailView(request, projekt_id, firma_id):
# Wenn Projektadmin: Zeige Ordnerbaum mit Freigabestufen für die Firma
    if user_ist_projektadmin(request.user, projekt_id):
        # Hole Ordnerstruktur
        projekt = Projekt.objects.get(pk = projekt_id)
        liste_ordner = Ordner.objects.filter(projekt = projekt)
        ordner_root = Ordner.objects.get(projekt = projekt, ist_root_ordner = True)
        # Erstelle Instanz von Ordnerbau und befülle dict_ordnerbaum für context
        ordnerbaum_instanz = Ordnerbaum()
        dict_ordnerbaum = ordnerbaum_instanz.erstelle_dict_ordnerbaum(liste_ordner, ordner_root)
        # Erstelle Liste mit Dictionaries aller Ordner mit Freigabestufen
        firma = Firma.objects.get(pk = firma_id)
        liste_ordner_freigabe = []
        for key, value in dict_ordnerbaum.items():
            ordner = value
            # Hole Eintrag in Ordner_Firma_Freigabe, wenn vorhanden, sonst erstelle Neuen Eintrag
            '''
            # TODO: 
            # Vorteil --> Es muüssen nicht alle Freigabe-Einträge neu erstellt wenn neuer Ordner od. Firma angelegt wird; 
            # Nachteil --> Evtl. Erzeugung von doppelten Einträgen möglich, oder Freigabe werden überschrieben?
            '''
            ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get_or_create(
                firma = firma, 
                ordner = ordner, 
                defaults={
                    'projekt':projekt,
                    'freigabe_lesen':False,
                    'freigabe_upload':False,
                    }
            )

            dict_ordner_freigabe = {}
            dict_ordner_freigabe['ordner_id'] = ordner.id
            dict_ordner_freigabe['ordner_darstellung'] = key
            dict_ordner_freigabe['ordner_freigabe_lesen'] = ordner_firma_freigabe[0].freigabe_lesen # Index erforderlich wegen 'get_or_create'
            dict_ordner_freigabe['ordner_freigabe_upload'] = ordner_firma_freigabe[0].freigabe_upload # Index erforderlich wegen 'get_or_create'
            liste_ordner_freigabe.append(dict_ordner_freigabe)

        # Leite Weiter zu Detailansicht Firma
        context = {
            'liste_ordner_freigabe':liste_ordner_freigabe,
            'firma':firma,
            'projekt_id':projekt_id
            }
        return render(request, 'firma_detail.html', context)

    # Wenn nicht Projektadmin: Zugriff verweigert
    else:
        return render(request, 'projektadmin_zugriff_verweigert.html')

def ordner_freigabe_ändern(request, projekt_id, firma_id):
# Wenn POST: Freigabe entsprechend Formulardaten ändern
# Wenn nicht POST passiert nichts

    if request.method == 'POST':
        projekt = Projekt.objects.get(pk = projekt_id)
        firma = Firma.objects.get(pk = firma_id)
        ordner_id = request.POST['ordner_id']
        ordner = Ordner.objects.get(pk = ordner_id)
        
        ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get(
            ordner = ordner,
            firma = firma
        )

        # Passe Freigaben entsprechende Daten in POST an

        if 'freigabe_lesen' in request.POST:
            ordner_firma_freigabe.freigabe_lesen = True
        else:
            ordner_firma_freigabe.freigabe_lesen = False
            
        if 'freigabe_upload' in request.POST:
            ordner_firma_freigabe.freigabe_upload = True
        else:
            ordner_firma_freigabe.freigabe_upload = False

        ordner_firma_freigabe.save()

        # Weiterleitung zu Detailansicht Firma
        return HttpResponseRedirect(reverse('projektadmin:firma_detail', args=[projekt_id, firma_id]))

################################################
# Views für Ordnerverwaltung

def ordnerÜbersichtView(request, projekt_id):
# Zeige Ordnerstruktur
# F. jdn Ordner Formular zum Hinzufügen von Unterordner
# F. jdn Ordner Formular zum Einstellen des Workflowschemas

    #Prüfen, ob Projektadmin
    if user_ist_projektadmin(request.user, projekt_id):
        # Hole Ordnerstruktur
        projekt = Projekt.objects.get(pk = projekt_id)
        liste_ordner = Ordner.objects.filter(projekt = projekt)
        ordner_root = Ordner.objects.get(projekt = projekt, ist_root_ordner = True)
        # Dropdownfeld für Workflowschema (Auswahlmöglichkeiten: WFSch für das Projekt)
        wfsch_wählen_form = WFSchWählenForm()
        wfsch_wählen_form.fields['wfsch'].queryset = Workflow_Schema.objects.filter(projekt = projekt)
        # Erstelle Instanz von Ordnerbau und befülle dict_ordnerbaum für context
        ordnerbaum_instanz = Ordnerbaum()
        dict_ordnerbaum = ordnerbaum_instanz.erstelle_dict_ordnerbaum(liste_ordner, ordner_root)
        # Befülle Context und Rendere Template für Ordnerübersicht
        context = {
            'dict_ordnerbaum':dict_ordnerbaum, # Muss als Funktion eingefügt werden, damit dict bei jedem Aufruf neu befüllt wird
            'wfsch_wählen_form':wfsch_wählen_form,
            'ordner_root':ordner_root,
            'projekt_id':projekt_id
        }
        return render(request, 'ordner_übersicht.html', context)

    # Wenn nicht Projektadmin Weiterleitung auf Zugriff-Vereweigert-Seite
    else:
        return render(request, 'projektadmin_zugriff_verweigert.html')

def ordnerNeuView(request, überordner_id):
# Wenn POST-Anfragen, dann erstelle neuen Ordner und leite zu Ordnerübersicht weiter
# Wenn keine POST-Anfrage, dann zeige Formular für Erstellen von neuem Ordner
    überordner = Ordner.objects.get(pk = überordner_id)
    projekt = überordner.projekt
    projekt_id = projekt.id

    # Prüfe ob Projektadmin
    if user_ist_projektadmin(request.user, projekt.id):
        
        # Wenn POST, dann erstelle Ordner
        if request.method == 'POST':
            neuer_ordner = Ordner.objects.create(
                bezeichnung = request.POST['bezeichnung'],
                projekt = projekt,
                ist_root_ordner = False,
                überordner = überordner
                )

            # Weiterleitung zur Ordnerübersicht
            return HttpResponseRedirect(reverse('projektadmin:ordner_übersicht', args=[projekt.id]))
        
        # Wenn nicht POST, dann zeige Formular für neuen Ordner
        else:
            
            context = {'projekt_id':projekt_id, 'überordner':überordner}
            return render(request, 'ordner_neu.html', context)

    # Wenn nicht Projektadmin Weiterleitung auf Zugriff-Vereweigert-Seite
    else:
        return render(request, 'projektadmin_zugriff_verweigert.html')

def wfschÄndernView(request):
# Wenn POST, dann aktualisiere WFSch für den Ordner
# Wenn nicht POST, dann passiert nichts
    ordner_id = request.POST['ordner_id']
    ordner = Ordner.objects.get(pk = ordner_id)
    projekt = ordner.projekt

    if request.method == 'POST':
        # Hole und validiere Formulardaten
        wfsch_ändern_daten = WFSchWählenForm(request.POST)
        if wfsch_ändern_daten.is_valid():
            # Ändere Workflowschema für den Ordner
            workflowschema = wfsch_ändern_daten.cleaned_data['wfsch']
            ordner.workflow_schema = workflowschema
            ordner.save()

        # Aktualisiere Ordnerübersicht
        return HttpResponseRedirect(reverse('projektadmin:ordner_übersicht', args=[projekt.id]))
    
    else:
        return HttpResponseRedirect(reverse('projektadmin:ordner_übersicht', args=[projekt.id]))
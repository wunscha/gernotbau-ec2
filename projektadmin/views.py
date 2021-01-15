from django.shortcuts import render
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import Workflow_Schema, Workflow_Schema_Stufe, WFSch_Stufe_Firma, Ordner, Ordner_Firma_Freigabe
from .forms import FirmaNeuForm, WFSchWählenForm
from superadmin.models import Projekt, Firma, Projekt_Firma_Mail
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from funktionen import hole_objs, hole_dicts

def übersicht_firmen_view(request, projekt_id):
    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Projektadmin
        if not user_ist_projektadmin(request.user, projekt_id):
            fehlermeldung = 'Melden Sie sich bitte als Projektadmin für das gewünschte Projekt an'
            context = {
                'fehlermeldung': fehlermeldung,
            }
            return render(request, './registration/login.html', context)
        else:

            projekt = Projekt.objects.using('default').get(pk = projekt_id)
            fehlermeldung = '' # Fehlermeldung für context
                
            # Wenn POST: Verbinde/Löse Projekt mit/von Firma aus Forumlardaten
            if request.method == 'POST':

                # Wenn Aufruf von "Firma lösen Formular": Entferne Verbindung Projekt-Firma aus Formulardaten
                if 'firma_lösen_id' in request.POST:
                    firma_lösen = Firma.objects.get(pk = request.POST['firma_lösen_id'])
                    projekt_firma_mail = Projekt_Firma_Mail.objects.get(projekt = projekt_id, firma = firma_lösen)
                    
                    # Wenn Projektadmin-Firma: Fehlermeldung für context
                    if projekt_firma_mail.ist_projektadmin:
                        fehlermeldung = 'Die Projektadmin-Firma kann nicht vom Projekt gelöst werden'
                        
                    else:
                        projekt_firma_mail.delete(using = 'default')

                    # TODO: Warnhinweis "Wollen Sie wirklich löschen?"

                # Wenn Aufruf von "Firma verbinden Formular": Verbinde Projekt mit Firma aus Forumlardaten
                if 'firma_verbinden_id' in request.POST:
                    firma = Firma.objects.using('default').get(pk = request.POST['firma_verbinden_id'])
                    neu_projekt_firma_mail = Projekt_Firma_Mail(
                        email = projekt.kurzbezeichnung + firma.email,
                        firma = firma, 
                        ist_projektadmin = False,
                        projekt = projekt
                    )
                    neu_projekt_firma_mail.save(using='default')

                    # Fehlermeldung für context leeren
                    fehlermeldung=''

                    # TODO: Log-Einträge
                    # TODO: InfoMails
            
            # Liste aller Firmen im Projekt für context
            liste_pj_fa_mail = Projekt_Firma_Mail.objects.filter(projekt = projekt)
            liste_firmen_projekt = []
            for eintrag in liste_pj_fa_mail:
                dict_firma = {}
                dict_firma['id'] = eintrag.firma.id
                dict_firma['bezeichnung'] = eintrag.firma.bezeichnung
                dict_firma['ist_projektadmin'] = eintrag.ist_projektadmin
                liste_firmen_projekt.append(dict_firma)
            
            # Liste aller Firmen, die nicht im Projekt sind für context
            liste_firmen_außerhalb_obj = Firma.objects.exclude(projekt = projekt)
            liste_firmen_außerhalb = []
            for firma in liste_firmen_außerhalb_obj:
                dict_firma = {}
                dict_firma['id'] = firma.id
                dict_firma['kurzbezeichnung'] = firma.kurzbezeichnung
                liste_firmen_außerhalb.append(dict_firma)
            
            # Lade Template
            context = {
                'fehlermeldung': fehlermeldung,
                'projekt_id': projekt_id,
                'liste_firmen_projekt': liste_firmen_projekt,
                'liste_firmen_außerhalb': liste_firmen_außerhalb,
            }
            return render(request, './projektadmin/übersicht_firmen.html', context)
            

################################################
# View für Workflows

def übersicht_workflowschemata(request, projekt_id):
    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Projektadmin
        if not user_ist_projektadmin(request.user, projekt_id):
            fehlermeldung = 'Melden Sie sich bitte als Projektadmin für das gewünschte Projekt an'
            context = {
                'fehlermeldung': fehlermeldung,
            }
            return render(request, './registration/login.html', context)
        else:

            projekt = Projekt.objects.using('default').get(pk = projekt_id)
            fehlermeldung = '' # Fehlermeldung für context

            # Wenn POST: 
            # - Füge Workflowschmea hinzu/ Entferne Workflowschema, oder
            # - Füge Stufe hinzu/ Entferne Stufe, oder
            # - Füge Prüffirma hinzu/ Entferne Prüffirma
            if request.method == 'POST':

                # Workflowschema erstellen
                if 'wfsch_neu_bezeichnung' in request.POST:
                    pass

                # Workflowschema löschen
                if 'wfsch_löschen_id' in request.POST:
                    pass

                # Workflowschema_Stufe hinzufügen
                if 'wfsch_stufe_neu_id' in request.POST:
                    pass
                
                # Workflowschema_Stufe löschen
                if 'wfsch_stufe_löschen_id' in request.POST:
                    pass
                
                # Prüffirma mit Stufe verbinden
                if 'prüffirma_verbinden_id' in request.POST:
                    pass
                
                # Prüffirma lösen
                if 'prüffirma_lösen_id' in request.POST:
                    pass
                
                # TODO: Weiterleitung zu Warnhinweis
                # TODO: Logs
                # TODO: Infomails

            # Erzeuge Liste Workflowschemata für context
            # Hole Workflowschemata
            liste_workflowschemata_obj = Workflow_Schema.objects.using(projekt_id).filter(projekt = projekt)
            liste_workflowschemata = []
            for workflow_schema in liste_workflowschemata_obj:
                # Hole Workflowschema Stufen
                liste_wfsch_stufen_obj = Workflow_Schema_Stufe.objects.using(projekt_id).filter(workflow_schema = workflow_schema)
                liste_wfsch_stufen_obj = sortierte_stufenliste(liste_wfsch_stufen_obj)
                liste_wfsch_stufen = []
                for wfsch_stufe in liste_wfsch_stufen_obj:
                    # Hole Prüffirmen
                    liste_prüffirmen = hole_dicts.prüffirmen(projekt, wfsch_stufe)
                    # Hole Firmen, die nicht in Stufe
                    liste_nicht_prüffirmen = hole_dicts.nicht_prüffirmen(projekt, wfsch_stufe)
                    
                    dict_wfsch_stufe = {}
                    dict_wfsch_stufe['liste_prüffirmen'] = liste_prüffirmen
                    dict_wfsch_stufe['liste_nicht_prüffirmen'] = liste_nicht_prüffirmen
                    dict_wfsch_stufe['id'] = wfsch_stufe.id
                    liste_wfsch_stufen.append(dict_wfsch_stufe)
                    
                dict_workflow_schema = {}
                dict_workflow_schema['liste_wfsch_stufen'] = liste_wfsch_stufen
                dict_workflow_schema['id'] = workflow_schema.id
                dict_workflow_schema['bezeichnung'] = workflow_schema.bezeichnung
                liste_workflowschemata.append(dict_workflow_schema)
            
            context = {
                'liste_workflowschemata': liste_workflowschemata,
                'projekt_id': projekt_id,
            }

            return render(request, './projektadmin/übersicht_workflowschemata.html', context)

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
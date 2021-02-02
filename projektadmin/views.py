from django.shortcuts import render
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import Workflow_Schema, Workflow_Schema_Stufe, WFSch_Stufe_Firma, Ordner, Ordner_Firma_Freigabe, Überordner_Unterordner
from .forms import FirmaNeuForm, WFSchWählenForm
from superadmin.models import Projekt, Firma, Projekt_Firma_Mail
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from funktionen import hole_objs, hole_dicts, workflows, ordnerfunktionen

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

                    # Ordnerfreigaben für die Firma löschen
                    ordnerfunktionen.lösche_ordnerfreigaben_firma(projekt, firma = firma_lösen)

                    # TODO: Warnhinweis "Wollen Sie wirklich löschen?"

                # Wenn Aufruf von "Firma verbinden Formular": Verbinde Projekt mit Firma aus Forumlardaten
                if 'firma_verbinden_id' in request.POST:
                    firma = Firma.objects.using('default').get(pk = request.POST['firma_verbinden_id'])
                    neu_projekt_firma_mail = Projekt_Firma_Mail(
                        email = projekt.kurzbezeichnung + '.' + firma.email, # TODO: Funktion für Prüfung auf vorhandene Mailadressen
                        firma = firma, 
                        ist_projektadmin = False,
                        projekt = projekt
                    )
                    neu_projekt_firma_mail.save(using='default')

                    # Ordnerfreigabe initialisieren
                    ordnerfunktionen.initialisiere_ordnerfreigaben_firma(projekt, firma = firma)

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
                    neues_workflowschema = Workflow_Schema(
                        bezeichnung = request.POST['wfsch_neu_bezeichnung']
                    )
                    neues_workflowschema.save(using = projekt_id)

                # Workflowschema löschen
                if 'wfsch_löschen_id' in request.POST:
                    wfsch_löschen = Workflow_Schema.objects.using(projekt_id).get(pk = request.POST['wfsch_löschen_id'])
                    wfsch_löschen.delete(using = projekt_id)

                # Workflowschema_Stufe hinzufügen
                if 'stufe_neu_wfsch_id' in request.POST:
                    workflow_schema = Workflow_Schema.objects.using(projekt_id).get(pk = request.POST['stufe_neu_wfsch_id'])
                    liste_stufen = workflows.hole_stufenliste(projekt, workflow_schema)
                    vorstufe = workflows.letzte_stufe(projekt, workflow_schema)
                    
                    neue_wfsch_stufe = Workflow_Schema_Stufe(
                        workflow_schema = workflow_schema,
                        vorstufe = vorstufe if liste_stufen else None,
                        bezeichnung = request.POST['wf_stufe_bezeichnung']
                    )
                    neue_wfsch_stufe.save(using = projekt_id)

                # Workflowschema_Stufe löschen
                if 'wfsch_stufe_löschen_id' in request.POST:
                    wfsch_stufe_löschen = Workflow_Schema_Stufe.objects.using(projekt_id).get(pk = request.POST['wfsch_stufe_löschen_id'])
                    
                    # Vorstufe der nächsten Stufe muss neu referenziert werden
                    nächste_st = workflows.nächste_stufe(projekt, wfsch_stufe_löschen)
                    if nächste_st:
                        nächste_st.vorstufe = wfsch_stufe_löschen.vorstufe
                        nächste_st.save(using = projekt_id)
                    wfsch_stufe_löschen.delete(using = projekt_id)
                
                # Prüffirma mit Stufe verbinden
                if 'prüffirma_verbinden_id' in request.POST:
                    wfsch_stufe_pf_verbinden = Workflow_Schema_Stufe.objects.using(projekt_id).get(pk = request.POST['pf_verbinden_wfsch_stufe_id'])
                    neu_wfsch_stufe_fa = WFSch_Stufe_Firma(
                        workflow_schema_stufe = wfsch_stufe_pf_verbinden,
                        firma_id = request.POST['prüffirma_verbinden_id']
                    )
                    neu_wfsch_stufe_fa.save(using = projekt_id)

                # Prüffirma lösen
                if 'prüffirma_lösen_id' in request.POST:
                    wfsch_stufe = Workflow_Schema_Stufe.objects.using(projekt_id).get(pk = request.POST['pf_lösen_wfsch_stufe_id'])
                    eintrag_wfsch_stufe_fa = WFSch_Stufe_Firma.objects.using(projekt_id).get(
                        workflow_schema_stufe = wfsch_stufe,
                        firma_id = request.POST['prüffirma_lösen_id']
                        )
                    eintrag_wfsch_stufe_fa.delete(using = projekt_id)
                
                # TODO: Weiterleitung zu Warnhinweis
                # TODO: Logs
                # TODO: Infomails

            # Erzeuge Liste Workflowschemata für context
            # Hole Workflowschemata
            liste_workflowschemata_obj = Workflow_Schema.objects.using(projekt_id).all()
            liste_workflowschemata = []
            for workflow_schema in liste_workflowschemata_obj:
                # Hole Workflowschema Stufen
                liste_wfsch_stufen_obj = workflows.sortierte_stufenliste(projekt, workflow_schema)
                liste_wfsch_stufen_obj = Workflow_Schema_Stufe.objects.using(projekt_id).filter(workflow_schema = workflow_schema)
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
                    dict_wfsch_stufe['vorstufe_id'] = wfsch_stufe.vorstufe.id if wfsch_stufe.vorstufe else None
                    liste_wfsch_stufen.append(dict_wfsch_stufe)
                    
                dict_workflow_schema = {}
                dict_workflow_schema['liste_wfsch_stufen'] = liste_wfsch_stufen
                dict_workflow_schema['id'] = workflow_schema.id
                dict_workflow_schema['bezeichnung'] = workflow_schema.bezeichnung
                liste_workflowschemata.append(dict_workflow_schema)
            
            # Packe context und lade Übersicht Workflowschemata
            context = {
                'liste_workflowschemata': liste_workflowschemata,
                'projekt_id': projekt_id,
            }

            return render(request, './projektadmin/übersicht_workflowschemata.html', context)

################################################
# Views für Ordnerverwaltung

def übersicht_ordner_view(request, projekt_id):

    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Projektadmin
        if not user_ist_projektadmin(request.user, projekt_id):
            fehlermeldung = 'Bitte Loggen Sie sich als Projektadministrator für das gewünschte Projekt ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)
        else:
            
            projekt = Projekt.objects.using('default').get(pk = projekt_id)
            # Wenn POST:
            # - Neuen Ordner anlegen/löschen
            # - Workflowschema zuordnen
            if request.method == 'POST':
                anwendungsfall = request.POST['anwendungsfall']

                if anwendungsfall == 'ordner_anlegen':
                    # Unterordner anlegen
                    neuer_ordner = Ordner(
                        bezeichnung = request.POST['unterordner_bezeichnung'],
                        ist_root_ordner = False,
                    )
                    neuer_ordner.save(using = projekt_id)
                    
                    # Unterordner bei Überordner registrieren 
                    # (nicht mittels 'add()'-Methode weil sonst symmetrische Beziehung entsteht, die zu Endlossschleife bei 'erzeuge_darstellung_ordnerbaum()' führt )
                    überordner = Ordner.objects.using(projekt_id).get(pk = request.POST['ordner_id'])
                    neuer_eintrag_überordner_unterordner = Überordner_Unterordner(unterordner = neuer_ordner, überordner = überordner)
                    neuer_eintrag_überordner_unterordner.save(using = projekt_id)
                
                    # Ordnerfreigaben anlegen
                    ordnerfunktionen.initialisiere_ordnerfreigaben_ordner(projekt, ordner = neuer_ordner)

                if anwendungsfall == 'ordner_löschen':
                    ordner_löschen = Ordner.objects.using(projekt_id).get(pk = request.POST['ordner_löschen_id'])
                    liste_ordner_löschen = hole_objs.unterordner(projekt, ordner = ordner_löschen)
                    liste_ordner_löschen.append(ordner_löschen)
                    # TODO: Kontrolle, ob Ordner inhalt hat (wird dzt nur durch on_delete.PROTECT übernommen)
                    
                    for löschkandidat in liste_ordner_löschen:
                        # TODO: Kontrolle, ob Ordner inhalt hat (wird dzt nur durch on_delete.PROTECT übernommen)
                        # Ordner löschen(Root-Ordner darf nicht gelöscht werden)
                        if not löschkandidat.ist_root_ordner:
                            löschkandidat.delete(using = projekt_id)
                            # Verknüpungen Überordner-Unterordner löschen
                            liste_einträge_überordner_unterordner = Überordner_Unterordner.objects.using(projekt_id).filter(überordner = löschkandidat)
                            for eintrag in liste_einträge_überordner_unterordner:
                                eintrag.delete(using = projekt_id)
                            # Ordnerfreigaben löschen
                            ordnerfunktionen.lösche_ordnerfreigaben_ordner(projekt, löschkandidat)

                    # TODO: Warnhinweis
                    
                if anwendungsfall == 'workflowschema_zuweisen':
                    workflowschema = Workflow_Schema.objects.using(projekt_id).get(pk = request.POST['workflowschema_id'])
                    wfsch_ordner = Ordner.objects.using(projekt_id).get(pk = request.POST['ordner_id'])
                    wfsch_ordner.workflow_schema = workflowschema
                    wfsch_ordner.save(using = projekt_id)

                # TODO: InfoMails

            # Packe context und lade Übersicht Workflowschemata
            root_ordner = Ordner.objects.using(projekt_id).get(ist_root_ordner = True)
            liste_ordner = ordnerfunktionen.erzeuge_darstellung_ordnerbaum(projekt, root_ordner = root_ordner)
            liste_workflowschemata = hole_dicts.workflowschemata(projekt)

            context = {
                'projekt_id': projekt_id,
                'root_ordner_id': root_ordner.id,
                'liste_ordner': liste_ordner,
                'liste_workflowschemata': liste_workflowschemata,
            }

            return render(request, './projektadmin/übersicht_ordner.html', context)
         
def freigabeverwaltung_ordner(request, firma_id, projekt_id):
    
    # Prüfung Login
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:
        
        # Prüfung Projektadmin
        if not user_ist_projektadmin(request.user, projekt_id):
            fehlermeldung = 'Bitte loggens Sie sich als Projektadmin für das gewünschte Projekt ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)
        else:
            projekt = Projekt.objects.using('default').get(pk = projekt_id)
            firma = Firma.objects.using('default').get(pk = firma_id)

            vererbt_text = ''

            # POST:
            # Aktualisiere Ordnerfreigaben
            if request.method == 'POST':
                for key, value in request.POST.items():
                    # Suche Freigabeeinstellungen in POST und aktualisiere in DB
                    if 'freigabe_' in key:
                        ordner_id = key.split('_')[1] # Extrahiere Ordner-ID aus key
                        ordner = Ordner.objects.using(projekt_id).get(pk = ordner_id)
                        freigabeeinstellung = Ordner_Firma_Freigabe.objects.using(projekt_id).get(firma_id = firma.id, ordner = ordner)

                        # "freigaben_erben" aus Formular übernehmen
                        key_freigabevererbung = 'freigaben_erben_' + ordner_id
                        freigabeeinstellung.freigaben_erben = True if key_freigabevererbung in request.POST.keys() else False
                        
                        if freigabeeinstellung.freigaben_erben:
                            überordner = hole_objs.überordner(projekt, ordner)
                            freigabe_überordner = Ordner_Firma_Freigabe.objects.using(projekt_id).get(ordner = überordner, firma_id = firma.id)
                            freigabeeinstellung.freigabe_lesen = freigabe_überordner.freigabe_lesen
                            freigabeeinstellung.freigabe_upload = freigabe_überordner.freigabe_upload
                            freigabeeinstellung.save(using = projekt_id)

                        # Wenn keine Vererbung eingestellt: Freigabeeinstellungen aus Formular übernehmen
                        else:
                            if value == 'lesefreigabe':
                                freigabeeinstellung.freigabe_lesen = True
                                freigabeeinstellung.freigabe_upload = False
                            elif value == 'uploadfreigabe':
                                freigabeeinstellung.freigabe_lesen = False
                                freigabeeinstellung.freigabe_upload = True
                            else:
                                freigabeeinstellung.freigabe_lesen = False
                                freigabeeinstellung.freigabe_upload = False

                            freigabeeinstellung.save(using = projekt_id)
                    
            # Packe Context und Lade Übersicht
            root_ordner = Ordner.objects.using(projekt_id).get(ist_root_ordner = True)
            liste_ordner = ordnerfunktionen.erzeuge_darstellung_ordnerbaum(
                projekt = projekt, 
                root_ordner = root_ordner,
                firma = firma
            )

            context = {
                'vererbt_text': vererbt_text,
                'firma': firma.__dict__,
                'projekt_id': projekt_id,
                'liste_ordner': liste_ordner,
            }

            return render(request, './projektadmin/freigabeverwaltung_ordner.html', context)
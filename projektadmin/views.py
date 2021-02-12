from django.shortcuts import render
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import V_Workflow_Schema, WFSch_Stufe_Rolle, Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Firma, Ordner, Ordner_Firma_Freigabe
from .forms import FirmaNeuForm, WFSchWählenForm

from superadmin.models import Projekt, Firma
from projektadmin.models import Rolle, liste_rollen_dict, liste_rollen
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from funktionen import hole_objs, hole_dicts, workflows, ordnerfunktionen
from gernotbau.settings import DB_SUPER

def zugriff_verweigert_projektadmin(request, projekt_id):
    if not user_ist_projektadmin(request.user, projekt_id):
        fehlermeldung = 'Melden Sie sich bitte als Projektadmin für das gewünschte Projekt an'
        context = {'fehlermeldung': fehlermeldung}
        return render(request, './registration/login.html', context)


# NEUE VIEW (11.02.2021)
def firma_anlegen_view(request, projekt_id):
    projekt = Projekt.objects.using('default').get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung(DB_SUPER)
    erfolgsmeldung = ''

    # TODO: Kontrolle LogIn
    # TODO: Kontrolle Projektadmin

    if request.method == 'POST':
        neue_firma = projekt.firma_anlegen(DB_SUPER, formulardaten = request.POST, ist_projektadmin = False)
        erfolgsmeldung = 'Firma "' + neue_firma.bezeichnung(DB_SUPER) + '" wurde angelegt.'

        return HttpResponseRedirect(reverse('projektadmin:übersicht_firmen', args = [projekt_id]))

    # Packe Context und Lade Template
    context = {
        'liste_rollen': liste_rollen_dict(db_projekt),
        'projekt_id': projekt_id,
        'erfolgsmeldung': erfolgsmeldung
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
            projekt.firma_verbinden(db_bezeichnung = DB_SUPER, firma = fa)

        # EREIGNIS FIRMA LÖSEN
        if request.POST['ereignis'] == 'firma_lösen':
            fa = Firma.objects.using(DB_SUPER).get(pk = request.POST['firma_id'])
            projekt.firma_lösen(db_bezeichnung = DB_SUPER, firma = fa)

    # Packe Context und Lade Template
    context = {
        'projekt_id': projekt_id,
        'liste_projektfirmen': projekt.liste_projektfirmen_dicts(DB_SUPER),
        'liste_nicht_projektfirmen': projekt.liste_nicht_projektfirmen_dicts(DB_SUPER),
        }

    return render(request, './projektadmin/übersicht_firmen.html', context)

def detailansicht_firma_view(request, projekt_id, firma_id):#
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)
    db_projekt = projekt.db_bezeichnung(DB_SUPER)

    # POST
    if request.method == 'POST':
        
        # EREIGNIS ROLLEN AKTUALISIEREN
        if request.POST['ereignis'] == 'rollen_aktualisieren':
            for r in liste_rollen(db_projekt):
                ist_firmenrolle = True if str(r.id) in request.POST else False
                r.ist_firmenrolle_ändern(db_projekt, firma, ist_firmenrolle)

        # EREIGNIS IST FIRMENADMIN AKTUALISIEREN
        if request.POST['ereignis'] == 'ist_projektadmin_aktualisieren':
            ist_projektadmin = True if 'ist_projektadmin' in request.POST else False
            firma.ist_projektadmin_ändern(DB_SUPER, projekt, ist_projektadmin)

    # Liste Rollen
    li_rollen_dict = []
    for r in liste_rollen(db_projekt):
        dict_r = r.dict_rolle(db_projekt)
        dict_r['ist_firmenrolle'] = r.ist_firmenrolle(db_projekt, firma)
        li_rollen_dict.append(r)
    
    # Packe Context und Lade Template
    context = {
        'projekt_id': projekt_id,
        'liste_rollen': li_rollen_dict,
        'firma': firma.firma_dict(DB_SUPER),
        'firma_ist_projektadmin': firma.ist_projektadmin(DB_SUPER, projekt)
        }

    return render(request, './projektadmin/detailansicht_firma.html', context)


################################################
# View für Workflows

# NEUE VIEW (11.02.2021)
def übersicht_wfsch_view(request, projekt_id):
    # TODO: Kontrolle LogIn
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using('default').get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung(DB_SUPER)

    # POST
    if request.method == 'POST':
        # EREIGNIS PRÜFFIRMA HINZUFÜGEN
        if request.POST['ereignis'] == 'prüffirma_hinzufügen':
            rolle = Rolle.objects.using(db_projekt).get(pk = request.POST['rolle_id'])
            wfsch_stufe = WFSch_Stufe.objects.using(db_projekt).get(pk = request.POST['wfsch_stufe_id'])
            wfsch_stufe.prüffirma_hinzufügen(db_bezeichnung = db_projekt, rolle = rolle, firma_id = request.POST['prüffirma_id'])

        # EREIGNIS PRÜFFIRMA LÖSEN
        if request.POST['ereignis'] == 'prüffirma_lösen':
            rolle = Rolle.objects.using(db_projekt).get(pk = request.POST['rolle_id'])
            wfsch_stufe = WFSch_Stufe.objects.using(db_projekt).get(pk = request.POST['wfsch_stufe_id'])
            wfsch_stufe.prüffirma_lösen(db_bezeichnung = db_projekt, rolle = rolle, firma_id = request.POST['prüffirma_id'])

        # EREIGNIS WFSCH LÖSCHEN
        if request.POST['ereignis'] == 'wfsch_löschen':
            wfsch = Workflow_Schema.objects.using(db_projekt).get(pk = request.POST['wfsch_id'])
            wfsch.löschen(db_bezeichnung = db_projekt)

        # EREIGNIS WFSCH VORLAGE ANLEGEN
        if request.POST['ereignis'] == 'wfsch_vorlage_anlegen':
            v_wfsch = V_Workflow_Schema.objects.using(DB_SUPER).get(pk = request.POST['v_wfsch_id'])
            v_wfsch.in_db_anlegen(db_bezeichnung_quelle = DB_SUPER, db_bezeichnung_ziel = db_projekt)

        # TODO: EREIGNIS STUFE HINZUFÜGEN/ENTFERNEN IMPLEMENTIEREN
        # TODO: EREIGNIS ROLLE HINZUFÜGEN/ENTFERNEN IMPLEMENTIEREN
        # TODO: EREIGNIS WFSCH HINZUFÜGEN/ENTFERNEN IMPLEMENTIEREN

    # Liste Vorlagen WFSch
    li_v_wfsch = []
    for v_wfsch in V_Workflow_Schema.objects.using(DB_SUPER).all():
        if not v_wfsch.gelöscht(DB_SUPER) and not v_wfsch.instanz(db_projekt):
            li_v_wfsch.append(v_wfsch.v_wfsch_dict(DB_SUPER))

    # Liste WFSch
    li_wfsch = []
    for wfsch in Workflow_Schema.objects.using(db_projekt).all():
        if not wfsch.gelöscht(db_projekt):
            li_wfsch.append(wfsch.wfsch_dict(DB_SUPER, db_projekt, projekt))
    
    context = {
        'projekt_id': projekt.id,
        'liste_v_wfsch': li_v_wfsch,
        'liste_wfsch': li_wfsch
        }

    return render(request, './projektadmin/übersicht_wfsch.html', context)

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
                        bezeichnung = request.POST['wfsch_stufe_bezeichnung']
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
                    
                    '''
                    AUSKOMMENTIERT WEGEN NEUER HERANGEHENSWEISE (08.02.2021)

                    # Unterordner bei Überordner registrieren 
                    # (nicht mittels 'add()'-Methode weil sonst symmetrische Beziehung entsteht, die zu Endlossschleife bei 'erzeuge_darstellung_ordnerbaum()' führt )
                    überordner = Ordner.objects.using(projekt_id).get(pk = request.POST['ordner_id'])
                    neuer_eintrag_überordner_unterordner = Überordner_Unterordner(unterordner = neuer_ordner, überordner = überordner)
                    neuer_eintrag_überordner_unterordner.save(using = projekt_id)
                    '''

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
                            
                            ''' 
                            AUSKOMMENTIER WEGEN NEUER HERANGEHENSWEISE 08.02.2021

                            # Verknüpungen Überordner-Unterordner löschen
                            liste_einträge_überordner_unterordner = Überordner_Unterordner.objects.using(projekt_id).filter(überordner = löschkandidat)
                            for eintrag in liste_einträge_überordner_unterordner:
                                eintrag.delete(using = projekt_id)
                            '''
                            
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
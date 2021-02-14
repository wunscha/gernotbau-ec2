from django.shortcuts import render
from .funktionen import user_ist_projektadmin, sortierte_stufenliste, suche_letzte_stufe, Ordnerbaum
from .models import Ordner_WFSch, Projektstruktur, V_Workflow_Schema, WFSch_Stufe_Rolle, Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Firma, Ordner, Ordner_Firma_Freigabe
from .forms import FirmaNeuForm, WFSchWählenForm
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.utils import timezone

from superadmin.models import Projekt, Firma
from projektadmin.models import V_Projektstruktur, Rolle, liste_rollen_dict, liste_rollen, liste_rollen_firma_dict, liste_ordner_dict, liste_ordner, liste_wfsch_dict, liste_v_pjs_dict
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
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung(DB_SUPER)

    # POST
    if request.method == 'POST':

        # EREIGNIS PJS IMPORTIEREN
        if request.POST['ereignis'] == 'pjs_importieren':
            pjs = V_Projektstruktur.objects.using(DB_SUPER).get(pk = request.POST['pjs_id'])
            pjs.in_db_anlegen(DB_SUPER, db_projekt)

        # EREIGNIS ORDNER LÖSCHEN
        if request.POST['ereignis'] == 'ordner_löschen':
            ordner = Ordner.objects.using(db_projekt).get(pk = request.POST['ordner_id'])
            ordner.löschen(db_projekt)

        # EREIGNIS ORDNER ANLEGEN
        if request.POST['ereignis'] == 'ordner_anlegen':
            neuer_ordner = Ordner.objects.using(db_projekt).create(
                zeitstempel = timezone.now()
                )
            neuer_ordner.bezeichnung_ändern(db_projekt, request.POST['ordner_bezeichnung'])
            neuer_ordner.entlöschen(db_projekt)

        # EREIGNIS UNTERORDNER ANLEGEN
        if request.POST['ereignis'] == 'unterordner_anlegen':
            ordner = Ordner.objects.using(db_projekt).get(pk = request.POST['ordner_id'])
            ordner.unterordner_anlegen(db_projekt, request.POST['unterordner_bezeichnung'])

        # EREIGNIS WFSCH ÄNDERN
        if request.POST['ereignis'] == 'wfsch_ändern':
            ordner = Ordner.objects.using(db_projekt).get(pk = request.POST['ordner_id'])
            if request.POST['wfsch_id'] == 'Kein WFSch':
                ordner.verbindung_wfsch_löschen(db_projekt)    
            else:
                wfsch = Workflow_Schema.objects.using(db_projekt).get(pk = request.POST['wfsch_id'])
                ordner.verbindung_wfsch_herstellen(db_projekt, wfsch)

    # Packe context und lade Template
    context = {
        'projekt_id': projekt_id,
        'liste_ordner': liste_ordner_dict(DB_SUPER, db_projekt),
        'liste_wfsch': liste_wfsch_dict(db_projekt),
        'liste_v_pjs': liste_v_pjs_dict(DB_SUPER) if not Projektstruktur.objects.using(db_projekt).all() else None # Nur ausfüllen wenn noch keine PJS importiert
        } 
    
    return render(request, './projektadmin/übersicht_ordner.html', context)

def freigabeverwaltung_ordner_view(request, firma_id, projekt_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Projektadmin

    projekt = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    db_projekt = projekt.db_bezeichnung(DB_SUPER)
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    if request.method == 'POST':
        # EREIGNIS FREIGABEN AKTUALISIEREN
        if request.POST['ereignis'] == 'aktualisieren':
            for key, value in request.POST.items():
                if 'freigabe' in value:
                    ordner = Ordner.objects.using(db_projekt).get(pk = key)
                    if value == 'freigabe_lesen':
                        ordner.lesefreigabe_erteilen_firma(db_projekt, firma)
                    elif value == 'freigabe_upload':
                        ordner.uploadfreigabe_erteilen_firma(db_projekt, firma)
                    else:
                        ordner.freigaben_entziehen_firma(db_projekt, firma)

        # EREIGNIS FREIGABEN ÜBERNEHMEN ROLLE
        if request.POST['ereignis'] == 'freigaben_rollen_übernehmen':
            for o in liste_ordner(db_projekt):
                o.freigaben_übertragen_rollen_firma(db_projekt, firma)

    li_ordner_dict = []
    for o in liste_ordner(db_projekt):
        dict_o = o.ordner_dict(DB_SUPER, db_projekt)
        dict_o['freigabe_lesen'] = True if o.lesefreigabe_firma(db_projekt, firma) else False
        dict_o['freigabe_upload'] = True if o.uploadfreigabe_firma(db_projekt, firma) else False
        dict_o['keine_freigabe'] = True if not dict_o['freigabe_lesen'] and not dict_o['freigabe_upload'] else False
        li_ordner_dict.append(dict_o)
    
    # Packe Context und lade Template
    dict_firma = firma.firma_dict(DB_SUPER)
    dict_firma['liste_rollen'] = liste_rollen_firma_dict(db_projekt, firma)

    context = {
        'projekt_id': projekt_id,
        'firma': dict_firma,
        'liste_ordner': li_ordner_dict,
        }

    return render(request, './projektadmin/freigabeverwaltung_ordner.html', context)
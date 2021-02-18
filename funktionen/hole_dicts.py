from django.contrib.auth import get_user_model

from dokab.models import Dokument, Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status
from superadmin.models import Firma, Mitarbeiter, Projekt
from projektadmin.models import Ordner, Ordner_Firma_Freigabe, WFSch_Stufe_Mitarbeiter, Workflow_Schema, WFSch_Stufe_Firma, WFSch_Stufe
from . import hole_objs
from . import workflows
from .workflows import wf_stufe_ist_aktuell
from .hole_objs import aktueller_prüferstatus_wf_stufe

def projekte_user(user):
# Gibt Liste mit Dictionaries aller Projekte von user zurück
    liste_projekte_user_objs = hole_objs.projekte_user(user)

    liste_projekte_user = []
    for projekt in liste_projekte_user_objs:
        liste_projekte_user.append(projekt.__dict__)

    return liste_projekte_user

# TODO: Kann mit funktion 'projekte_mitarbeiter' zusammengelegt werden

def projekte_user_projektadmin(user):
# Gibt Liste mit Dictionaries aller Projekte zurück, für die user Projektadmin ist
    liste_projekte_user_projektadmin_objs = hole_objs.projekte_user_projektadmin(user)

    liste_projekte_user_projektadmin = []
    for projekt in liste_projekte_user_projektadmin_objs:
        liste_projekte_user_projektadmin.append(projekt.__dict__)

    return liste_projekte_user_projektadmin

# TODO: Kann mit funktion 'projekte_mitarbeiter' zusammengelegt werden

def projektfirmen(projekt):
# Gibt Liste mit Dictionaries aller Projektfirmen zurück
    liste_projektfirmen_obj = Firma.objects.using('default').filter(projekt = projekt)
    
    liste_dicts_projektfirmen = []
    for firma in liste_projektfirmen_obj:
        liste_dicts_projektfirmen.append(firma.__dict__)
    
    return liste_dicts_projektfirmen

def nicht_projektfirmen(projekt):
# Gibt Liste mit Dictionaries aller Firmen zurück, die nicht beim Projekt sind
    liste_nicht_projektfirmen_obj = Firma.objects.using('default').all().exclude(projekt = projekt)

    liste_dicts_nicht_projektfirmen = []
    for firma in liste_nicht_projektfirmen_obj:
        liste_dicts_nicht_projektfirmen.append(firma.__dict__)

    return liste_dicts_nicht_projektfirmen

def prüffirmen(projekt, wfsch_stufe):
# Gibt Liste mit Dictionaries aller Firmen zurück, die Prüffirma für wfsch_stufe sind
    liste_prüffirmen = hole_objs.prüffirmen(projekt, wfsch_stufe)

    liste_dicts_prüffirmen = []
    for prüffirma in liste_prüffirmen:
        prüffirma = Firma.objects.using('default').get(pk = prüffirma.id)
        liste_dicts_prüffirmen.append(prüffirma.__dict__)

    return liste_dicts_prüffirmen

def nicht_prüffirmen(projekt, wfsch_stufe):
# Gibt Liste mit Dictionaries aller Firmen zurück, die nicht Prüffirma für die wfsch_stufe sind
    liste_nicht_prüffirmen_obj = hole_objs.nicht_prüffirmen(projekt, wfsch_stufe)
    
    liste_dicts_nicht_prüffirmen = []
    for prüffirma in liste_nicht_prüffirmen_obj:
        liste_dicts_nicht_prüffirmen.append(prüffirma.__dict__)

    return liste_dicts_nicht_prüffirmen

def workflowschemata(projekt):
# Gibt Liste mit Dictionaries der Workflowschemata zurück
    qs_workflowschemata = Workflow_Schema.objects.using(str(projekt.id)).all()

    liste_workflowschemata = []
    for workflowschema in qs_workflowschemata:
        liste_workflowschemata.append(workflowschema.__dict__)
    
    return liste_workflowschemata

def projekte_mitarbeiter(mitarbeiter):
# Gibt Liste mit Dictionaries der Projekte eines Mitarbeiters zurück
    qs_projekte_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').filter(mitarbeiter = mitarbeiter)

    liste_projekte = []
    for eintrag in qs_projekte_ma_mail:
        liste_projekte.append(eintrag.projekt.__dict__)

    return liste_projekte

def firmenmitarbeiter(*, firma):
# Gibt Liste mit Dictionaries der Mitarbeiter von firma zurück
    qs_mitarbeiter = Mitarbeiter.objects.using('default').filter(firma = firma)

    liste_mitarbeiter = []
    for mitarbeiter in qs_mitarbeiter:
        if mitarbeiter.aktiv:
            dict_mitarbeiter = mitarbeiter.__dict__
            dict_mitarbeiter['liste_projekte'] = projekte_mitarbeiter(mitarbeiter) # Liste Projeke als Dict

            liste_mitarbeiter.append(dict_mitarbeiter)
    
    return liste_mitarbeiter

def projektfirma(*, projekt, firma):
# Gibt dict für die Firma inklusive projektmailadresse, Liste der Nicht-/Projektmitarbeiter und 'ist_projektadmin' zurück
    dict_projektfirma = firma.__dict__
    
    eintrag_pj_fa_mail = Projekt_Firma_Mail.objects.using('default').get(firma = firma, projekt = projekt)
    dict_projektfirma['ist_projektadmin'] = eintrag_pj_fa_mail.ist_projektadmin
    dict_projektfirma['projektmail'] = eintrag_pj_fa_mail.email
    dict_projektfirma['liste_projektmitarbeiter'] = liste_projektmitarbeiter_firma(projekt = projekt, firma = firma)
    dict_projektfirma['liste_nicht_projektmitarbeiter'] = liste_nicht_projektmitarbeiter_firma(projekt = projekt, firma = firma)

    return dict_projektfirma

def firmenprojekt(*, projekt, firma):
# Gibt dict für ein Firmenprojekt inklusive projektmailadresse, Liste der Nicht-/Projektmitarbeiter und 'ist_projektadmin' zurück
    dict_firmenprojekt = projekt.__dict__
    
    eintrag_pj_fa_mail = Projekt_Firma_Mail.objects.using('default').get(firma = firma, projekt = projekt)
    dict_firmenprojekt['firma_ist_projektadmin'] = eintrag_pj_fa_mail.ist_projektadmin
    dict_firmenprojekt['projektmail'] = eintrag_pj_fa_mail.email
    dict_firmenprojekt['liste_projektmitarbeiter'] = liste_projektmitarbeiter_firma(projekt = projekt, firma = firma)
    dict_firmenprojekt['liste_nicht_projektmitarbeiter'] = liste_nicht_projektmitarbeiter_firma(projekt = projekt, firma = firma)

    return dict_firmenprojekt

def liste_projekte_firma(*, firma):
# Gibt Liste mit Dictionaries der Projekte und zugeordneten Mitarbeiter für firma zurück
    qs_projekte = Projekt.objects.using('default').filter(firma = firma)

    liste_projekte = []
    for projekt in qs_projekte:
        dict_projekt = firmenprojekt(projekt = projekt, firma = firma)
        liste_projekte.append(dict_projekt)

    return liste_projekte

def projektmitarbeiter(*, mitarbeiter, projekt):
# Gibt dict des Mitarbeiters mitsamt projektmail und ist_projektadmin zurück

    eintrag = Projekt_Mitarbeiter_Mail.objects.using('default').get(mitarbeiter = mitarbeiter, projekt = projekt)
    dict_mitarbeiter = eintrag.mitarbeiter.__dict__
    dict_mitarbeiter['ist_projektadmin'] = eintrag.ist_projektadmin
    dict_mitarbeiter['projektmail'] = eintrag.email

    return dict_mitarbeiter

def liste_projektmitarbeiter_firma(*, projekt, firma):
# Gibt die Liste aller Mitarbeiter von firma zurück, die bei projekt sind
    li_projektmitarbeiter_firma_objs = hole_objs.liste_projektmitarbeiter_firma(projekt = projekt, firma = firma)

    li_projektmitarbeiter_firma_dicts = []
    for pjma in li_projektmitarbeiter_firma_objs:
        dict_pjma = pjma.__dict__
        eintrag_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').get(mitarbeiter = pjma, projekt = projekt)
        dict_pjma['ist_projektadmin'] = eintrag_pj_ma_mail.ist_projektadmin
        dict_pjma['projektmail'] = eintrag_pj_ma_mail.email
        li_projektmitarbeiter_firma_dicts.append(dict_pjma)

    return li_projektmitarbeiter_firma_dicts

def liste_nicht_projektmitarbeiter_firma(*, projekt, firma):
# Gibt Liste aller Mitarbeiter von firma, die nicht bei projekt sind, zurück
    li_nicht_projektmitarbeiter_firma_objs = hole_objs.liste_nicht_projektmitarbeiter_firma(projekt = projekt, firma = firma)
    
    li_nicht_projektmitarbeiter_firma_dicts = []
    for nicht_pjma in li_nicht_projektmitarbeiter_firma_objs:
        li_nicht_projektmitarbeiter_firma_dicts.append(nicht_pjma.__dict__)


    return li_nicht_projektmitarbeiter_firma_dicts

def liste_prüfer_fa_wfsch_stufe(*, projekt, wfsch_stufe, firma):
# Gibt Liste mit dicts der Prüfer von firma für wfsch_stufe zurück (inkl. 'immer erforderlich')
    qs_einträge_wfsch_stufe_ma = WFSch_Stufe_Mitarbeiter.objects.using(str(projekt.id)).filter(wfsch_stufe = wfsch_stufe)

    li_prüfer_fa = []
    for eintrag in qs_einträge_wfsch_stufe_ma:
        prüfer = Mitarbeiter.objects.using('default').get(pk = eintrag.mitarbeiter_id)
        if prüfer.firma == firma:
            dict_prüfer = prüfer.__dict__
            dict_prüfer['immer_erforderlich'] = eintrag.immer_erforderlich
            li_prüfer_fa.append(dict_prüfer)
    
    return li_prüfer_fa

def liste_nicht_prüfer_wfsch_stufe(*, projekt, wfsch_stufe, firma):
# Gibt Liste mit dicts aller Firmenmitarbeier zurück, die nicht Prüfer für wfsch_stufe sind
    
    # Hole Alle Prüfer von firma für wfsch_stufe
    qs_einträge_wfsch_stufe_ma = WFSch_Stufe_Mitarbeiter.objects.using(str(projekt.id)).filter(wfsch_stufe = wfsch_stufe)
    li_prüfer = []
    for eintrag in qs_einträge_wfsch_stufe_ma:
        prüfer = Mitarbeiter.objects.using('default').get(pk = eintrag.mitarbeiter_id)
        li_prüfer.append(prüfer)
    
    # Sortiere Firmenmitarbeiter aus, die nicht Prüfer für wfsch_stufe sind
    li_nicht_prüfer = []
    qs_firmenmitarbeier = Mitarbeiter.objects.using('default').filter(firma = firma, aktiv = True, ist_firmenadmin = False)
    for ma in qs_firmenmitarbeier:
        if ma not in li_prüfer:
            li_nicht_prüfer.append(ma.__dict__)

    return li_nicht_prüfer

def liste_prüffirmen_wfsch_stufe(*, projekt, wfsch_stufe):
# Gibt Liste mit dicts der Prüffirmen für eine WFSch-Stufe zurück (inkl. Prüfer)
    qs_einträge_wfsch_stufe_fa = WFSch_Stufe_Firma.objects.using(str(projekt.id)).filter(workflow_schema_stufe = wfsch_stufe)

    li_prüffirmen = []
    for eintrag in qs_einträge_wfsch_stufe_fa:
        prüffirma = Firma.objects.using('default').get(pk = eintrag.firma_id)
        dict_prüffirma = prüffirma.__dict__
        
        li_prüfer = liste_prüfer_fa_wfsch_stufe(projekt = projekt, wfsch_stufe = wfsch_stufe, firma = prüffirma)
        dict_prüffirma['liste_prüfer'] = li_prüfer
        
        li_nicht_prüfer = liste_nicht_prüfer_wfsch_stufe(projekt = projekt, wfsch_stufe = wfsch_stufe, firma = prüffirma)
        dict_prüffirma['liste_nicht_prüfer'] = li_nicht_prüfer

        li_prüffirmen.append(dict_prüffirma)
    
    return li_prüffirmen


def liste_wfsch_stufen(*, projekt, wfsch):
# Gibt Liste mit dicts der WFSch-Stufen von wfsch zurück (inkl. Prüffirmen)
    qs_wfsch_stufen = Workflow_Schema_Stufe.objects.using(str(projekt.id)).filter(workflow_schema = wfsch)
    # qs_wfsch_stufen = workflows.sortierte_stufenliste(projekt, wfsch)
    # TODO: Stufenliste sortieren

    li_wfsch_stufen = []
    for wfsch_st in qs_wfsch_stufen:
        dict_wfsch_stufe = wfsch_st.__dict__
        dict_wfsch_stufe['liste_prüffirmen'] = liste_prüffirmen_wfsch_stufe(projekt = projekt, wfsch_stufe = wfsch_st)
        li_wfsch_stufen.append(dict_wfsch_stufe)
    
    return li_wfsch_stufen

def liste_wfsch_firma(*, firma):
# Gibt Liste der WFSch zurück, für die die Firma Prüffirma ist

    li_wfsch = hole_objs.liste_wfsch_firma(firma = firma)

    li_wfsch_firma = []
    for wfsch in li_wfsch:
        projekt = Projekt.objects.using('default').get(pk = wfsch['projekt_id'])
        dict_wfsch = wfsch['wfsch'].__dict__ # wfsch wird von 'liste_wfsch_firma' als dict{'projekt_id', 'wfsch'} übergeben
        dict_wfsch['projekt_id'] = wfsch['projekt_id']
        dict_wfsch['liste_wfsch_stufen'] = liste_wfsch_stufen(projekt = projekt, wfsch = wfsch['wfsch'])

        li_wfsch_firma.append(dict_wfsch)

    return li_wfsch_firma

def ordner_mit_freigaben(*, projekt, firma, ordner):
# Gibt dict für Ordner inkl. Freigaben für firma zurück
    dict_ordner = ordner.__dict__

    # Freigaben hinzufügen
    eintrag_ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.using(str(projekt.id)).get(ordner = ordner, firma_id = firma.id)
    dict_ordner['freigabe_lesen'] = eintrag_ordner_firma_freigabe.freigabe_lesen
    dict_ordner['freigabe_upload'] = eintrag_ordner_firma_freigabe.freigabe_upload
    dict_ordner['freigaben_erben'] = eintrag_ordner_firma_freigabe.freigaben_erben
    dict_ordner['firma_id'] = eintrag_ordner_firma_freigabe.firma_id

    return dict_ordner

def liste_ordner(*, projekt, firma):
# Gibt Liste mit Dicts für alle Projektordner inkl. Freigaben für firma zurück
    qs_ordner = Ordner.objects.using(str(projekt.id)).all()

    li_ordner = []
    for o in qs_ordner:
        dict_ordner = ordner_mit_freigaben(projekt = projekt, firma = firma, ordner = o)
        li_ordner.append(dict_ordner)
    
    return li_ordner

def liste_unterordner(*, projekt, firma, ordner):
# Gibt Liste mit Dicts für alle Unterordner von ordner inkl. Freigaben für firma zurück
    li_ordner = []
    for o in ordner.unterordner.all():
        dict_ordner = ordner_mit_freigaben(projekt = projekt, firma = firma, ordner = o)
        li_ordner.append(dict_ordner)
    
    return li_ordner

def dokument_mit_wfsch(*, projekt, dokument):
# Gibt dict für Dokument inkl. Felder für Workflow zurück
    dict_dokument = dokument.__dict__
    
    # WF-Schema hinzufügen, wenn WF vorhanden
    workflow_dokument_vorhanden = Workflow.objects.using(str(projekt.id)).filter(dokument = dokument)
    if workflow_dokument_vorhanden:
        dict_dokument['wf_schema'] = dokument.workflow.workflow_schema.bezeichnung if dokument.workflow != None else None

    # Name Dokumenteninhaber hinzufügen
    mitarbeiter = Mitarbeiter.objects.using('default').get(pk = dokument.mitarbeiter_id)
    dict_dokument['name_mitarbeiter'] = mitarbeiter.first_name + ' ' + mitarbeiter.last_name

    return dict_dokument

def liste_dokumente_ordner(*, projekt, ordner):
# Gibt Liste mit dicts der Dokumente in ordner zurück (inkl. WF-Stati)
    qs_dokumente = Dokument.objects.using(str(projekt.id)).filter(ordner = ordner)
    
    li_dokumente = []
    for dok in qs_dokumente:
        dict_dokument = dokument_mit_wfsch(projekt = projekt, dokument = dok)
        li_dokumente.append(dict_dokument)

    return li_dokumente

def liste_prüfer_fa_wf_stufe(*, projekt, wf_stufe, firma):
# Gibt Liste mit dicts der Prüfer von firma für wfsch_stufe zurück (inkl. dict_status und 'immer erforderlich')
    qs_einträge_wf_stufe_ma = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(wf_stufe = wf_stufe)

    li_prüfer_fa = []
    for eintrag in qs_einträge_wf_stufe_ma:
        prüfer = Mitarbeiter.objects.using('default').get(pk = eintrag.mitarbeiter_id)
        if prüfer.firma == firma:
            dict_prüfer = prüfer.__dict__
            dict_prüfer['immer_erforderlich'] = eintrag.immer_erforderlich
            dict_prüfer['prüferstatus'] = eintrag.status.__dict__
            li_prüfer_fa.append(dict_prüfer)
    
    return li_prüfer_fa

########################################################
# EXPERIMENTE MIT DEKORATOREN/VERSCHACHTELTEN FUNKTIONEN

def liste_prüfer_wf_stufe_firma(*, projekt, wf_stufe, firma):
# Gibt Liste der Prüfer für wf_stufe zurück, die zur firma gehören, inklusive Status
    li_prüfer_obj = hole_objs.liste_prüfer_wf_stufe_firma(projekt = projekt, wf_stufe = wf_stufe, firma = firma)

    li_prüfer_dict = []
    for p in li_prüfer_obj:
        dict_prüfer = p.__dict__

        eintrag_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).get(
            workflow_stufe = wf_stufe, 
            mitarbeiter_id = p.id
            )
        dict_prüfer['immer_erforderlich'] = eintrag_ma_stufe_status.immer_erforderlich

        dict_prüfer['prüferstatus'] = aktueller_prüferstatus_wf_stufe(projekt = projekt, prüfer = p, wf_stufe = wf_stufe).__dict__

        li_prüfer_dict.append(dict_prüfer)
    
    return li_prüfer_dict

def liste_prüffirmen_wf_stufe(*, projekt, wf_stufe):
# Gibt Liste der Prüffirmen für wf_stufe zurück (inkl. Liste Prüfer und Liste Firmenstati)
    li_prüffirmen_obj = hole_objs.liste_prüffirmen_wf_stufe(projekt = projekt, wf_stufe = wf_stufe)

    li_prüffirmen_dict = []
    for pf in li_prüffirmen_obj:
        # Dict für Prüffirma anlegen
        dict_prüffirma = pf.__dict__

        # Firmenstatus hinzufügen
        status_pf = workflows.firmenstatus(
                    projekt = projekt, 
                    wf_stufe = wf_stufe,
                    prüffirma = pf
                    )
        dict_prüffirma['firmenstatus'] = status_pf.__dict__
        
        # Liste Prüfer von pf hinzufügen
        dict_prüffirma['liste_prüfer'] = liste_prüfer_wf_stufe_firma(projekt = projekt, wf_stufe = wf_stufe, firma = pf)

        # Liste erweitern
        li_prüffirmen_dict.append(dict_prüffirma)

    return li_prüffirmen_dict

def liste_workflows(*, projekt, liste_wf_obj):
# Wandelt liste_wf_obj in eine verschachtelte Liste aus Dictionaries um (inkl. Infos zu Stati etc.)
    
    li_workflows = []
    for wf in liste_wf_obj:
        # Liste Workflowstufen
        qs_wf_stufen = Workflow_Stufe.objects.using(str(projekt.id)).filter(workflow = wf)

        li_wf_stufen = []
        for s in qs_wf_stufen:
            # Dict wf_stufe packen und an liste_wf_stufen anhängen
            dict_wf_stufe = s.__dict__

            # Liste Prüffirmen inkl. Firmenstati
            li_prüffirmen = liste_prüffirmen_wf_stufe(projekt = projekt, wf_stufe = s)
            dict_wf_stufe['liste_prüffirmen'] = li_prüffirmen
            
            # Stufenstatus ermitteln
            status_stufe = workflows.stufenstatus(projekt = projekt, wf_stufe = s)
            dict_wf_stufe['dict_stufenstatus'] = status_stufe.__dict__

            # Stufe aktuell?
            dict_wf_stufe['aktuell'] = wf_stufe_ist_aktuell(projekt = projekt, wf_stufe = s)

            li_wf_stufen.append(dict_wf_stufe)

        # Dict worfklow packen und an liste_worfklows ahnhängen
        dict_workflow = wf.__dict__
        dict_workflow['workflowschema'] = wf.workflow_schema.__dict__
        dict_workflow['dokument'] = wf.dokument.__dict__
        dict_workflow['liste_wf_stufen'] = li_wf_stufen

        li_workflows.append(dict_workflow)

    return li_workflows
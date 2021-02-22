from django.contrib.auth import get_user, get_user_model

from funktionen.workflows import wf_ist_abgeschlossen, wf_stufe_ist_aktuell
from superadmin.models import Mitarbeiter, Firma, Projekt
from projektadmin.models import WFSch_Stufe_Firma

# TODO: 'gelöscht'-Logik implementieren

def projekte_user(user):
# Gibt Liste aller Projekte von user zurück
    qs_projekt_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').filter(mitarbeiter = user)
    
    liste_projekte_user = []
    for eintrag in qs_projekt_ma_mail:
        liste_projekte_user.append(eintrag.projekt)
    
    return liste_projekte_user

def projekte_user_projektadmin(user):
# Gibt Liste aller Projekte zurück für die user Projektadmin ist
    qs_projekt_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').filter(
        mitarbeiter = user, 
        ist_projektadmin = True
        )

    liste_projekte_user_projektadmin = []
    for eintrag in qs_projekt_ma_mail:
        liste_projekte_user_projektadmin.append(eintrag.projekt)

    return liste_projekte_user_projektadmin

def prüffirmen(projekt, wfsch_stufe):
# Gibt Liste mit allen Prüffirmen für wfsch_stufe zurück
    liste_wfsch_stufe_firma = WFSch_Stufe_Firma.objects.using(str(projekt.id)).filter(workflow_schema_stufe = wfsch_stufe)

    liste_prüffirmen_wfsch_stufe = []
    for eintrag in liste_wfsch_stufe_firma:
        firma = Firma.objects.using('default').get(pk = eintrag.firma_id)
        liste_prüffirmen_wfsch_stufe.append(firma)
    
    return liste_prüffirmen_wfsch_stufe

def nicht_prüffirmen(projekt, wfsch_stufe):
# Gibt Liste mit Firmen zurück, die nicht Prüffirma für wfsch_stufe sind
    liste_projektfirmen = Firma.objects.using('default').filter(projekt = projekt)
    liste_prüffirmen = prüffirmen(projekt, wfsch_stufe)
    liste_nicht_prüffirmen = [firma for firma in liste_projektfirmen if firma not in liste_prüffirmen]
    
    return liste_nicht_prüffirmen

'''
AUSKOMMENTIERT WEGEN NEUER HERANGEHENSWEISE 08.02.2021

def unterordner(projekt, ordner):
# Gibt Liste mit den Unterordnern von ordner zurück
    qs_einträge_überordner_unterordner = Überordner_Unterordner.objects.using(str(projekt.id)).filter(überordner = ordner)
    
    liste_unterordner = []
    for eintrag in qs_einträge_überordner_unterordner:
        liste_unterordner.append(eintrag.unterordner)
    
    return liste_unterordner

def überordner(projekt, ordner):
# Gibt den Überordner für ordner zurück
    qs_einträge_überordner_unterordner = Überordner_Unterordner.objects.using(str(projekt.id)).all()

    überordner = None
    for eintrag in qs_einträge_überordner_unterordner:
        if eintrag.unterordner == ordner:
            überordner = eintrag.überordner

    return überordner

'''

def liste_projektmitarbeiter(*, projekt):
# Gibt Liste mit allen Mitarbeitern zurück, die bei projekt sind
    qs_einträge_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').filter(projekt = projekt)

    liste_projektmitarbeiter = []
    for eintrag in qs_einträge_pj_ma_mail:
        liste_projektmitarbeiter.append(eintrag.mitarbeiter)

    return liste_projektmitarbeiter

def liste_nicht_projektmitarbeiter(*, projekt):
# Gibt Liste mit allen Mitarbeitern zurück, die nicht bei projekt sind
    qs_alle_mitarbeiter = Mitarbeiter.objects.using('default').all()
    li_projektmitarbeiter = liste_projektmitarbeiter(projekt = projekt)

    li_nicht_projektmitarbeiter = []
    for ma in qs_alle_mitarbeiter:
        if ma not in li_projektmitarbeiter:
            li_nicht_projektmitarbeiter.append(ma)
    
    return li_nicht_projektmitarbeiter

def liste_projektmitarbeiter_firma(*, projekt, firma):
# Gibt alle Mitarbeiter von firma zurück, die bei projekt sind
    qs_einträge_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.using('default').filter(
        mitarbeiter__aktiv = True, 
        mitarbeiter__firma = firma,
        mitarbeiter__ist_firmenadmin = False, 
        projekt = projekt
        )

    li_projektmitarbeiter_firma = []
    for eintrag in qs_einträge_pj_ma_mail:
        li_projektmitarbeiter_firma.append(eintrag.mitarbeiter)

    return li_projektmitarbeiter_firma

def liste_nicht_projektmitarbeiter_firma(*, projekt, firma):
# Gibt Liste mit allen Mitarbeitern von firma zurück, die nicht bei projekt sind
    qs_alle_firmenmitarbeiter = Mitarbeiter.objects.using('default').filter(aktiv = True, ist_firmenadmin = False, firma = firma)
    li_projektmitarbeiter_firma = liste_projektmitarbeiter_firma(projekt = projekt, firma = firma)

    li_nicht_projektmitarbeiter_firma = []
    for ma in qs_alle_firmenmitarbeiter:
        if ma not in li_projektmitarbeiter_firma:
            li_nicht_projektmitarbeiter_firma.append(ma)

    return li_nicht_projektmitarbeiter_firma

def liste_wfsch_firma(*, firma):
# Gibt Liste aller WFsch zurück, für die firma Prüffirma ist
# ...Rückgabe als Dict {'projekt_id', 'wfsch'}
    
    # Durchsuche alle Projekte nach wfsch für firma
    qs_projekte = Projekt.objects.using('default').all()
    li_wfsch_firma = []
    
    for projekt in qs_projekte:
        qs_einträge_wfsch_stufe_fa = WFSch_Stufe_Firma.objects.using(str(projekt.id)).filter(firma_id = str(firma.id))
        
        for eintrag in qs_einträge_wfsch_stufe_fa:
            wfsch = eintrag.workflow_schema_stufe.workflow_schema
            if wfsch not in li_wfsch_firma:
                dict_wfsch = {}
                dict_wfsch['wfsch'] = wfsch
                dict_wfsch['projekt_id'] = str(projekt.id)
                li_wfsch_firma.append(dict_wfsch)
    
    return li_wfsch_firma

def liste_prüffirmen_wf_stufe(*, projekt, wf_stufe):
# Gibt Liste der Prüffirmen für wf_stufe zurück
    qs_einträge_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(workflow_stufe = wf_stufe)

    # Liste anlegen
    User = get_user_model()
    li_firmen = []
    for eintrag in qs_einträge_ma_stufe_status:
        prüfer = User.objects.using('default').get(pk = eintrag.mitarbeiter_id)
        if prüfer.firma not in li_firmen:
            li_firmen.append(prüfer.firma)

    return li_firmen

def liste_prüfer_wf_stufe_firma(*, projekt, wf_stufe, firma):
# Gibt Liste aller Prüfer für wf_stufe zurück, die zu firma gehören
    qs_einträge_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(workflow_stufe = wf_stufe)

    User = get_user_model()
    li_prüfer = []
    for eintrag in qs_einträge_ma_stufe_status:
        prüfer = User.objects.using('default').get(pk = eintrag.mitarbeiter_id)
        if prüfer.firma == firma:
            li_prüfer.append(prüfer)
    
    return li_prüfer

def liste_wf_zur_bearbeitung(request, *, projekt):
# Gibt Liste der Workflows zurück, für die request.user Prüfer ist
    qs_einträge_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(mitarbeiter_id = request.user.id)
    
    li_wf_user_ist_prüfer = []
    for eintrag in qs_einträge_ma_stufe_status:
        if wf_stufe_ist_aktuell(projekt = projekt, wf_stufe = eintrag.workflow_stufe):
            wf = eintrag.workflow_stufe.workflow
            if wf not in li_wf_user_ist_prüfer and not wf_ist_abgeschlossen(projekt = projekt, workflow = wf):
                li_wf_user_ist_prüfer.append(wf)

    return li_wf_user_ist_prüfer

def filtere_aktive_wf(*, projekt, liste_wf_obj):
# Filtert Workflows aus liste_wf_obj, die nicht abgeschlossen sind und gibt Liste zurück
    li_aktive_wf = []
    for wf in liste_wf_obj:
        wf_abgeschlossen = WF_Update_Abgeschlossen.objects.using(str(projekt.id)).filter(workflow = wf).latest('zeitstempel').abgeschlossen
        if not wf_abgeschlossen:
            li_aktive_wf.append(wf)
    
    return li_aktive_wf

def aktuelle_wf_stufe(*, projekt, workflow):
# Gibt die aktuelle Stufe für workflow zurück
    qs_wf_stufe_update_aktuell = WF_Stufe_Update_Aktuell.objects.using(str(projekt.id)).filter(workflow_stufe__workflow = workflow, aktuell = True)
    return qs_wf_stufe_update_aktuell.latest('zeitstempel').workflow_stufe

def aktueller_prüferstatus_wf_stufe(*, projekt, prüfer, wf_stufe):
# Gibt den aktuellen Status von prüfer für wf_stufe zurück
    qs_einträge_stati = MA_Stufe_Status_Update_Status.objects.using(str(projekt.id)).filter(
        ma_stufe_status__mitarbeiter_id = prüfer.id,
        ma_stufe_status__workflow_stufe = wf_stufe)
    
    return qs_einträge_stati.latest('zeitstempel').status
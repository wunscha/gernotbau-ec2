from superadmin.models import Mitarbeiter, Firma, Projekt, Projekt_Firma_Mail, Projekt_Mitarbeiter_Mail
from projektadmin.models import WFSch_Stufe_Firma, Überordner_Unterordner

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


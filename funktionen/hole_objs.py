from superadmin.models import Firma, Projekt, Projekt_Mitarbeiter_Mail
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

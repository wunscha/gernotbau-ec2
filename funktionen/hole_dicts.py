from superadmin.models import Firma, Mitarbeiter, Projekt_Mitarbeiter_Mail
from projektadmin.models import Workflow_Schema, WFSch_Stufe_Firma
from . import hole_objs

def projekte_user(user):
# Gibt Liste mit Dictionaries aller Projekte von user zurück
    liste_projekte_user_objs = hole_objs.projekte_user(user)

    liste_projekte_user = []
    for projekt in liste_projekte_user_objs:
        liste_projekte_user.append(projekt.__dict__)

    return liste_projekte_user

def projekte_user_projektadmin(user):
# Gibt Liste mit Dictionaries aller Projekte zurück, für die user Projektadmin ist
    liste_projekte_user_projektadmin_objs = hole_objs.projekte_user_projektadmin(user)

    liste_projekte_user_projektadmin = []
    for projekt in liste_projekte_user_projektadmin_objs:
        liste_projekte_user_projektadmin.append(projekt.__dict__)

    return liste_projekte_user_projektadmin

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
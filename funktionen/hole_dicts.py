from superadmin.models import Firma
from projektadmin.models import WFSch_Stufe_Firma
from . import hole_objs

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
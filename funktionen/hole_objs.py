from superadmin.models import Firma
from projektadmin.models import WFSch_Stufe_Firma

def prüffirmen(projekt, wfsch_stufe):
# Gibt Liste mit allen Prüffirmen für wfsch_stufe zurück
    liste_wfsch_stufe_firma = WFSch_Stufe_Firma.using(projekt.id).filter(workflow_schema_stufe = wfsch_stufe)

    liste_prüffirmen_wfsch_stufe = []
    for eintrag in liste_wfsch_stufe_firma:
        firma = Firma.objects.using('default').get(pk = eintrag.firma_id)
        liste_prüffirmen_wfsch_stufe.append(firma)
    
    return liste_prüffirmen_wfsch_stufe

def nicht_prüffirmen(projekt, wfsch_stufe):
# Gibt Liste mit Firmen zurück, die nicht Prüffirma für wfsch_stufe sind
    liste_projektfirmen = Firma.objects.using('default').get(projekt = projekt)
    liste_nicht_projektfirmen = liste_projektfirmen.difference(prüffirmen(projekt, wfsch_stufe))

    return liste_nicht_projektfirmen


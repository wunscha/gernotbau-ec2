from projektadmin.models import Ordner, Überordner_Unterordner, Ordner_Firma_Freigabe
from funktionen import hole_objs

def erzeuge_ordnerbaum_dicts(root_ordner):
# Legt ein verschachtelte Dictionary nach der Struktur des Ordnerbaums an
    
    dict_ordnerbaum = {}
    dict_ordnerbaum['bezeichnung'] = root_ordner.bezeichnung

    # Rufe für jeden Unterordner rekursiv die Funktion auf und hänge alle Unterordner als dict an Liste Unterordner an
    liste_unterordner = []
    for ordner in root_ordner.unterordner.all():
        liste_unterordner.append(erzeuge_ordnerbaum_dicts(ordner))
    
    dict_ordnerbaum['liste_unterordner'] = liste_unterordner

    return dict_ordnerbaum

def erzeuge_darstellung_ordnerbaum(projekt, root_ordner, liste_ordner = [], ebenendarstellung = '...', ebene = 0, firma = None):
# Hängt Dictionaries für die Darstellung des Ordnerbaums von root_ordner an liste_ordner (leere Liste) und gibt sie zurück
    
    # Innere Funktion notwendig, damit liste_ordner bei jedem neuen Aufruf von äußerer Funktion geleert werden kann
    def erzeuge_darstellung_ordnerbaum_inner(projekt, überordner, liste_ordner = liste_ordner, ebenendarstellung = ebenendarstellung, ebene = ebene):
        if not überordner.ist_root_ordner:
            dict_ordner = überordner.__dict__
            dict_ordner['darstellung'] = ebene * ebenendarstellung
            dict_ordner['workflowschema_bezeichnung'] = überordner.workflow_schema.bezeichnung if überordner.workflow_schema else None
            
            if firma:
                freigabestufe = Ordner_Firma_Freigabe.objects.using(str(projekt.id)).get(firma = firma, ordner = überordner)
                dict_ordner['freigabe_lesen'] = freigabestufe.freigabe_lesen
                dict_ordner['freigabe_upload'] = freigabestufe.freigabe_upload
            
            liste_ordner.append(dict_ordner)
            ebene += 1

        # Hole Liste Unterordner:
        liste_unterordner = hole_objs.unterordner(projekt = projekt, ordner = überordner)

        for ordner in liste_unterordner:
            erzeuge_darstellung_ordnerbaum_inner(projekt = projekt, überordner = ordner, ebene = ebene)
        
        return liste_ordner
    
    # Leeren und neu befüllen von liste_ordner
    liste_ordner.clear()
    liste_ordner = erzeuge_darstellung_ordnerbaum_inner(projekt = projekt, überordner = root_ordner)
    
    return liste_ordner

'''
def initialisiere_ordnerfreigabe_firma(projekt, firma):
# Initialisiere für alle Ordner die Ordnerfreigabeeinstellung für firma, wenn noch nicht vorhanden

    qs_ordner = Ordner.objects.using(str(projekt.id)).all()

    if qs_ordner:
        for ordner in qs_ordner:
            freigabeeinstellung = Ordner_Firma_Freigabe.objects.get(ordner = ordner, firma_id = firma.id)
'''
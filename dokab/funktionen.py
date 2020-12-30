from superadmin.models import Firma, Projekt
from projektadmin.models import Ordner, Ordner_Firma_Freigabe
from dokab.models import Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status
from dokab import views

def user_hat_ordnerzugriff(user, ordner_id, projekt_id):
# Überprüfe, ob User Ordnerzugriff hat (Lese- und/oder Uploadfreigabe)
    firma = user.firma
    ordner = Ordner.objects.get(pk = ordner_id)
    projekt = Projekt.objects.get(pk = projekt_id)

    # Hole Eintrag in Ordner_Firma_Freigabe, wenn vorhanden, sonst erstelle Neuen Eintrag
    '''
    # TODO: 
    # Vorteil --> Es muüssen nicht alle Freigabe-Einträge neu erstellt wenn neuer Ordner od. Firma angelegt wird; 
    # Nachteil --> Evtl. Erzeugung von doppelten Einträgen möglich, oder Freigabe werden überschrieben?
    '''
    ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get_or_create(
        firma = firma, 
        ordner = ordner, 
        defaults = {
            'projekt':projekt, 
            'freigabe_lesen':False, 
            'freigabe_upload':False
            }
        )
    
    if ordner_firma_freigabe[0].freigabe_lesen or ordner_firma_freigabe[0].freigabe_upload: # Index erforderlich wegen 'get_or_create'
        return True
    else:
        return False

###################################
# DATEIEN

def speichere_datei_chunks(datei, zielpfad):
    with open(zielpfad + datei.name, 'wb+') as ziel:
        for chunk in datei.chunks():
            ziel.write(chunk)

###################################
# WORKFLOWS

def workflow_stufe_ist_aktuell(workflow_stufe):
# Stufe ist aktiv, wenn Aktuelle Stufe nicht abgeschlossen und vorige schon
    if not workflow_stufe.abgeschlossen:
        # Stufe ist aktuell, wenn Vorstufe abgeschlossen, sonst nicht
        if workflow_stufe.vorstufe:
            if workflow_stufe.vorstufe.abgeschlossen:
                return True
            else:
                return False
        # Wenn keine Vorstufe, dann ist Stufe erste Stufe (und daher aktuell, weil nicht abgeschlossen)
        return True
    else:
        return False

def stufenstatus_firma(workflow_stufe, firma):
# Gib den Status für die Firma anhand der Stati der einzelenen Prüfer zurück

    liste_wfsch_stufe_mitarbeiter = Mitarbeiter_Stufe_Status.objects.filter(mitarbeiter__firma = firma, workflow_stufe = workflow_stufe)
    
    # Prüfe ob Abgelehnt
    for wfsch_stufe_mitarbeiter in liste_wfsch_stufe_mitarbeiter:
        if wfsch_stufe_mitarbeiter.status == views.STATI['abgelehnt']:
            return views.STATI['abgelehnt']
    
    # Prüfe ob Rückfrage
    for wfsch_stufe_mitarbeiter in liste_wfsch_stufe_mitarbeiter:
        if wfsch_stufe_mitarbeiter.status == views.STATI['rückfrage']:
            return views.STATI['rückfrage']
    
    # Prüfe ob Warten auf Vorstufe
    for wfsch_stufe_mitarbeiter in liste_wfsch_stufe_mitarbeiter:
        if wfsch_stufe_mitarbeiter.status == views.STATI['warten_auf_vorstufe']:
            return views.STATI['warten_auf_vorstufe']

    # Prüfe ob Freigegeben
    stufenstatus_firma = views.STATI['in_bearbeitung']
    for wfsch_stufe_mitarbeiter in liste_wfsch_stufe_mitarbeiter:

        # Bei Freigabe Prüfer: Stufenstatus = Freigabe
        if wfsch_stufe_mitarbeiter.status == views.STATI['freigegeben']:
            stufenstatus_firma = views.STATI['freigegeben']

        # Wenn erforderlicher Prüfer fehlt: keine Freigabe
        elif wfsch_stufe_mitarbeiter.immer_erforderlich:
            return view.STATI['in_bearbeitung']

    return stufenstatus_firma

def liste_prüffirmen(workflow_stufe):
# Gib Liste mit allen Prfüffirmen der Workflow-Stufe zurück
    liste_prüffirmen = []
    liste_prüfer = workflow_stufe.mitarbeiter

    for prüfer in liste_prüfer:
        if prüfer.firma not in liste_prüffirmen:
            liste_prüffirmen.append(prüfer.firma)
    
    return liste_prüffirmen
            
from superadmin.models import Firma, Projekt
from projektadmin.models import Ordner, Ordner_Firma_Freigabe

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
#########################################################
# Funktionen für Workflowschema-Stufen

from .models import Workflow_Schema, Workflow_Schema_Stufe
from superadmin.models import Projekt, Projekt_Mitarbeiter_Mail

#Gib die WFSCh-Stufe zurück, die die aktuelle Stufe als Vorstufe hat
def suche_nächste_stufe(*,liste_stufen, aktuelle_stufe):
    nächste_stufe = ''

    #Stufe mit aktueller Stufe als Vorstufe wird zur nächsten Stufe
    for stufe in liste_stufen:
        if stufe.vorstufe == aktuelle_stufe:
                if nächste_stufe == '':
                    nächste_stufe = stufe
                #Fehler, wenn mehrer Stufen mit derselben Vorstufe
                else:
                    raise Exception('Mehrere Stufen mit derselben Vorstufe vorhanden!')

    return nächste_stufe

#Suche erste WFSch-Stufe (also die Stufe, die keine Vorstufe hat)
def suche_erste_stufe(liste_stufen):
    erste_stufe = ''
    
    #Stufe ohne Vorstufe wird zur ersten Stufe
    for stufe in liste_stufen:
        if not stufe.vorstufe:
            if erste_stufe == '':
                erste_stufe = stufe
            #Fehler, wenn mehrere Stufen ohne Vorstufe vorhanden
            else:
                raise Exception('Mehrere Anfangsstufen vorhanden')

    #Fehler, wenn keine erste Stufe gefunden wurde
    # if erste_stufe == '':
    #    raise Exception('Es konnte keine Anfangsstufe gefunden werden')
    return erste_stufe

# Suche letzte Stufe (also die Stufe, die für keine Stufe Vorstufe ist)
def suche_letzte_stufe(liste_stufen):
    liste_vorstufen = []
    letzte_stufe = ''
    
    # Liste mit allen Vorstufen erstellen
    for stufe in liste_stufen:
        liste_vorstufen.append(stufe.vorstufe)
    for stufe in liste_stufen:
        if not (stufe in liste_vorstufen):
            if letzte_stufe == '':
                letzte_stufe = stufe
            #Fehler, wenn mehrere 'letzte Stufen' vorhanden
            else:
                raise Exception('Mehrere Letzte Stufen vorhanden')
    
    # Fehler, wenn keine letzte Stufe gefunden wurde
    # if letzte_stufe == '':
    #    raise Exception('Es konnte keine letzte Stufe gefunden werden')

    return letzte_stufe

# Gibt sortierte Version einer Liste von Stufen aus
def sortierte_stufenliste(liste_stufen):
    sortierte_stufenliste = []
    nächste_stufe = suche_erste_stufe(liste_stufen)

    #Solange es nächste Stufe gibt, hänge nächste Stufe an
    while nächste_stufe:
        sortierte_stufenliste.append(nächste_stufe)
        aktuelle_stufe = nächste_stufe
        nächste_stufe = suche_nächste_stufe(liste_stufen = liste_stufen, aktuelle_stufe = aktuelle_stufe)

    return sortierte_stufenliste

#########################################################
# Hilfsfunktionen für Authentifizierung

# Prüft ob User Projektadmin ist
def user_ist_projektadmin(user, projekt_id):
    projekt = Projekt.objects.get(pk=projekt_id)
    # Hole Eintrag für Projekt-Mitarbeiter-ManyToMany-Beziehung aus der Through-Tabelle
    # und gib Wert für 'ist_projektadmin' zurück.
    pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.filter(mitarbeiter = user, projekt = projekt)[0]
    if pj_ma_mail:
        return pj_ma_mail.ist_projektadmin
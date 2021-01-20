from projektadmin.models import Workflow_Schema_Stufe
from dokab.models import Workflow_Stufe

def hole_stufenliste(projekt, workflow_workflowschema):
# Gibt die Liste der Stufen eines Workflows bzw. eines WF-Schemas zurück
    
    # Hole Stufenliste für worfklow == Workflow-Schema
    if workflow_workflowschema.__class__.__name__ == 'Workflow_Schema':
        liste_stufen = Workflow_Schema_Stufe.objects.using(str(projekt.id)).filter(workflow_schema = workflow_workflowschema)

    # Hole Stufenliste für workflow == Workflow
    if workflow_workflowschema.__class__.__name__ == 'Workflow':
        liste_stufen = Workflow_Stufe.objects.using(str(projekt.id)).filter(workflow = workflow_workflowschema)

    return liste_stufen

def nächste_stufe(projekt, aktuelle_stufe):
# Gibt die Stufe zurück, die die aktuelle Stufe als Vorstufe hat
    liste_stufen = Workflow_Schema_Stufe.objects.using('5').filter(workflow_schema = aktuelle_stufe.workflow_schema)
    
    '''
    # Hole Stufenliste, wenn WFSch-Stufe
    if aktuelle_stufe.__class__.__name__ == 'Worfklow_Schema_Stufe':
        workflow_schema = aktuelle_stufe.workflow_schema
        liste_stufen.append('WFSch_Stufe') # Workflow_Schema_Stufe.objects.using(str(projekt.id)).filter(workflow_schema = workflow_schema)

    # Hole Stufenliste, wenn WF-Stufe
    if aktuelle_stufe.__class__.__name__ == 'Workflow_Stufe':
        workflow = aktuelle_stufe.workflow
        liste_stufen.append('WF_Stufe') # Workflow_Stufe.objects.using(str(projekt.id)).filter(workflow = workflow)
    '''

    # Stufe mit aktueller Stufe als Vorstufe wird zur nächsten Stufe
    nächste_stufe = None
    for stufe in liste_stufen:
        if stufe.vorstufe == aktuelle_stufe:
                # if not nächste_stufe:
                    nächste_stufe = stufe
                #Fehler, wenn mehrer Stufen mit derselben Vorstufe
                # else:
                    # raise Exception('Mehrere Stufen mit derselben Vorstufe vorhanden!')

    return nächste_stufe

def erste_stufe(projekt, workflow):
# Gibt erste Stufe zurück (also die Stufe, die keine Vorstufe hat)
    liste_stufen = hole_stufenliste(projekt, workflow)
    
    # Stufe ohne Vorstufe wird zur ersten Stufe
    erste_stufe = ''
    for stufe in liste_stufen:
        if not stufe.vorstufe:
            if erste_stufe == '':
                erste_stufe = stufe
            # Fehler, wenn mehrere Stufen ohne Vorstufe vorhanden
            else:
                raise Exception('Mehrere Anfangsstufen vorhanden')

    return erste_stufe

def letzte_stufe(projekt, workflow):
# Gibt letzte Stufe zurück (also die Stufe, die für keine Stufe Vorstufe ist)
    liste_stufen = hole_stufenliste(projekt, workflow)

    # Wenn 
        
    # Liste mit allen Vorstufen erstellen
    liste_vorstufen = []
    for stufe in liste_stufen:
        liste_vorstufen.append(stufe.vorstufe)

    # Ermitteln, welche Stufe für keine Stufe Vorstufe ist
    letzte_stufe = ''
    for stufe in liste_stufen:
        if not (stufe in liste_vorstufen):
            if letzte_stufe == '':
                letzte_stufe = stufe
            #Fehler, wenn mehrere 'letzte Stufen' vorhanden
            else:
                raise Exception('Mehrere Letzte Stufen vorhanden')
    
    return letzte_stufe

def sortierte_stufenliste(projekt, workflow):
# Gibt sortierte Version einer Liste von Stufen aus
    
    #Solange es nächste Stufe gibt, hänge nächste Stufe an
    nächste_st = erste_stufe(projekt, workflow)
    sortierte_stufenliste = []
    while nächste_st:
        sortierte_stufenliste.append(nächste_stufe)
        aktuelle_stufe = nächste_st
        nächste_st = nächste_stufe(projekt, aktuelle_stufe)

    return sortierte_stufenliste
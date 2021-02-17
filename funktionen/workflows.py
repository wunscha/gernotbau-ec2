from funktionen import hole_objs
from projektadmin.models import WFSch_Stufe_Firma, WFSch_Stufe_Mitarbeiter, WFSch_Stufe
from superadmin.models import Firma
from dokab.models import Mitarbeiter_Stufe_Status, MA_Stufe_Status_Update_Status, WF_Update_Abgeschlossen, Workflow_Stufe, WF_Stufe_Update_Aktuell, Workflow, Status
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

def hole_stufenliste(projekt, workflow_workflowschema):
# Gibt die Liste der Stufen eines Workflows bzw. eines WF-Schemas zurück
    
    # Hole Stufenliste für worfklow == Workflow-Schema
    if workflow_workflowschema.__class__.__name__ == 'Workflow_Schema':
        liste_stufen = Workflow_Schema_Stufe.objects.using(str(projekt.id)).filter(workflow_schema = workflow_workflowschema)

    # Hole Stufenliste für workflow == Workflow
    elif workflow_workflowschema.__class__.__name__ == 'Workflow':
        liste_stufen = Workflow_Stufe.objects.using(str(projekt.id)).filter(workflow = workflow_workflowschema)

    else:
        liste_stufen = []

    return liste_stufen

def nächste_stufe(projekt, aktuelle_stufe):
# Gibt die Stufe zurück, die die aktuelle Stufe als Vorstufe hat
    qs_stufen = Workflow_Schema_Stufe.objects.using(str(projekt.id)).filter(workflow_schema = aktuelle_stufe.workflow_schema)
    
    # Stufe mit aktueller Stufe als Vorstufe wird zur nächsten Stufe
    nächste_stufe = None
    for stufe in qs_stufen:
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
    li_stufen_sortiert = []
    while nächste_st:
        li_stufen_sortiert.append(nächste_stufe)
        aktuelle_stufe = nächste_st
        nächste_st = nächste_stufe(projekt, aktuelle_stufe)

    return li_stufen_sortiert

def nächste_wfsch_stufe(*, projekt, wfsch_stufe):
    qs_wfsch_stufen = Workflow_Schema_Stufe.objects.using(str(projekt.id)).filter(
        workflow_schema = wfsch_stufe.workflow_schema
        )

    # Gib Stufe zurück, die aktuelle Stufe als Vorstufe hat
    nächste_stufe = None
    for st in qs_wfsch_stufen:
        if st.vorstufe == wfsch_stufe:
            nächste_stufe = st
    
    return nächste_stufe

def neuer_workflow(projekt, dokument):
# Legt neuen Workflow für dokument an
    wfsch = dokument.ordner.workflow_schema
    
    if wfsch:
        # Neuen Workflow anlegen
        neuer_wf = Workflow(
            dokument = dokument,
            workflow_schema = wfsch,
            )
        neuer_wf.save(using = str(projekt.id))

        # Eintrag WF_Update_Abgeschlossen anlegen
        neuer_eintrag_wf_update_abgeschlossen = WF_Update_Abgeschlossen(workflow = neuer_wf, abgeschlossen = False, zeitstempel = timezone.now())
        neuer_eintrag_wf_update_abgeschlossen.save(using = str(projekt.id))

        # Anfangsstufe WFSch
        wfsch_st = Workflow_Schema_Stufe.objects.using(str(projekt.id)).get(
            workflow_schema = wfsch,
            vorstufe = None,
        )

        vorst = None
        # Neue WF-Stufe anlegen, solange nächste WF-Stufe vorhanden
        while wfsch_st:
            neue_wf_stufe = Workflow_Stufe(
                workflow = neuer_wf,
                vorstufe = vorst,
                bezeichnung = wfsch_st.bezeichnung
                )
            neue_wf_stufe.save(using = str(projekt.id))

            # Neuer Eintrag WF_Stufe_Update_Aktuell -> True wenn erste Stufe, sonst False
            neuer_eintrag_wf_stufe_update_aktuell = WF_Stufe_Update_Aktuell(
                workflow_stufe = neue_wf_stufe,
                aktuell = True if vorst == None else False,
                zeitstempel = timezone.now()
                )
            neuer_eintrag_wf_stufe_update_aktuell.save(using = str(projekt.id))

            # Prüfer verbinden
            qs_einträge_prüfer_wfschst = WFSch_Stufe_Mitarbeiter.objects.using(str(projekt.id)).filter(wfsch_stufe = wfsch_st)
            statusbezeichnung = 'In Bearbeitung' if vorst == None else 'Warten auf Vorstufe'
            
            for eintrag_ma in qs_einträge_prüfer_wfschst:
                neuer_eintrag_prüfer_wfst = Mitarbeiter_Stufe_Status(
                    mitarbeiter_id = eintrag_ma.mitarbeiter_id,
                    workflow_stufe = neue_wf_stufe,
                    immer_erforderlich = eintrag_ma.immer_erforderlich
                    )
                neuer_eintrag_prüfer_wfst.save(using = str(projekt.id))

                # Neuer Eintrag MA_Stufe_Status_Update_Status
                neuer_eintrag_status = MA_Stufe_Status_Update_Status(
                    ma_stufe_status = neuer_eintrag_prüfer_wfst,
                    status = Status.objects.using(str(projekt.id)).get(bezeichnung = statusbezeichnung),
                    zeitstempel = timezone.now()
                    )
                neuer_eintrag_status.save(using = str(projekt.id))
                    

            # TODO: InfoMails
            # TODO: Logs

            # Neue Stufe wird Vorstufe für nächsten Schleifendurchlauf
            vorst = neue_wf_stufe
            # Nächste wfsch_st holen
            wfsch_st = nächste_wfsch_stufe(projekt = projekt, wfsch_stufe = wfsch_st)

def nächste_wf_stufe(*, projekt, wf_stufe):
    qs_wfsch_stufen = Workflow_Stufe.objects.using(str(projekt.id)).filter(
        workflow = wf_stufe.workflow
        )

    # Gib Stufe zurück, die aktuelle Stufe als Vorstufe hat
    nächste_stufe = None
    for st in qs_wfsch_stufen:
        if st.vorstufe == wf_stufe:
            nächste_stufe = st
    
    return nächste_stufe

def status(*, projekt, statusbezeichnung):
# Gibt den Status mit 'statusbezeichnung' zurück
    return Status.objects.using(str(projekt.id)).get_or_create(bezeichnung = statusbezeichnung)[0] # Index wegen get_or_create

def wf_stufe_ist_aktuell(*, projekt, wf_stufe):
# Gibt zurück, ob wf_stufe aktuell ist
    return WF_Stufe_Update_Aktuell.objects.using(str(projekt.id)).filter(workflow_stufe = wf_stufe).latest('zeitstempel').aktuell

def wf_ist_abgeschlossen(*, projekt, workflow):
# Gibt zurück, ob wf abgeschlossen ist
    return WF_Update_Abgeschlossen.objects.using(str(projekt.id)).filter(workflow = workflow).latest('zeitstempel').abgeschlossen

def status_abgelehnt_vorhanden(*, projekt, liste_ma_stati):
# Gibt True zurück, wenn Status 'Abgelehnt' in liste_ma_stati gefunden wird
    status_abgelehnt = status(projekt = projekt, statusbezeichnung = 'Abgelehnt')
    for e in liste_ma_stati:
        if e.status == status_abgelehnt:
            return True
    
    # Wenn kein Status 'Abgelehnt' gefunden wurde -> False
    return False

def status_rückfrage_vorhanden(*, projekt, liste_ma_stati):
# Gibt True zurück, wenn Status 'Rückfrage' in liste_ma_stati gefunden wird
    status_rückfrage = status(projekt = projekt, statusbezeichnung = 'Rückfrage')
    for e in liste_ma_stati:
        if e.status == status_rückfrage:
            return True

    # Wenn kein Status 'Rückfrage' gefunden wurde -> False
    return False

def status_freigabe_vorhanden(*, projekt, liste_ma_stati):
# Gibt True zurück, wenn Status 'Freigabe' in liste_ma_stati gefunden wird
    status_freigabe = status(projekt = projekt, statusbezeichnung = 'Freigegeben')
    for e in liste_ma_stati:
        if e.status == status_freigabe:
            return True
    
    # Wenn kein Status 'Freigabe' gefunden wurde -> False
    return False

def erforderliche_freigaben_vorhanden(*, projekt, liste_ma_stati):
# Gibt True zurück, wenn alle Prüfer mit 'immer erforderlich' freigegeben haben
    status_freigabe = status(projekt = projekt, statusbezeichnung = 'Freigegeben')
    
    # Wenn Prüfer mit 'immer_eforderlich' vorhanden, der nicht freigegeben hat -> False
    for e in liste_ma_stati:
        if e.ma_stufe_status.immer_erforderlich and not e.status == status_freigabe:
            return False

    return True


def firmenstatus(*, projekt, wf_stufe, prüffirma):
# Gibt den Status der Prüffirma zurück
    li_mitarbeiter = hole_objs.liste_projektmitarbeiter_firma(projekt = projekt, firma = prüffirma)
    
    li_einträge_aktuelle_ma_stati = []
    for ma in li_mitarbeiter:
        try:
            eintrag_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).get( # Abfrage mittels filter um Fehlermeldung fehlende
                mitarbeiter_id = ma.id,
                workflow_stufe = wf_stufe,
                )
            eintrag_aktueller_ma_status = MA_Stufe_Status_Update_Status.objects.using(str(projekt.id)).filter(ma_stufe_status = eintrag_ma_stufe_status).latest('zeitstempel')
        except ObjectDoesNotExist:
            eintrag_aktueller_ma_status = None

        li_einträge_aktuelle_ma_stati.append(eintrag_aktueller_ma_status)
    
    STATI = {
        'freigegeben': status(projekt = projekt, statusbezeichnung = 'Freigegeben'),
        'abgelehnt': status(projekt = projekt, statusbezeichnung = 'Abgelehnt'),
        'in_bearbeitung': status(projekt = projekt, statusbezeichnung = 'In Bearbeitung'),
        'warten_auf_vorstufe': status(projekt = projekt, statusbezeichnung = 'Warten auf Vorstufe'),
        'rückfrage': status(projekt = projekt, statusbezeichnung = 'Rückfrage')
        }

    # Prüfen ob Abgelehnt
    if status_abgelehnt_vorhanden(projekt = projekt, liste_ma_stati = li_einträge_aktuelle_ma_stati):
        return STATI['abgelehnt']

    # Prüfen ob Rückfrage (Rückfrage hemmt Freigabe)
    if status_rückfrage_vorhanden(projekt = projekt, liste_ma_stati = li_einträge_aktuelle_ma_stati):
        return STATI['rückfrage']

    # Wenn alle erforderliche Freigaben bzw. mind. eine Freigabe vorhanden -> Freigegeben
    if status_freigabe_vorhanden(projekt = projekt, liste_ma_stati = li_einträge_aktuelle_ma_stati) and erforderliche_freigaben_vorhanden(projekt = projekt, liste_ma_stati = li_einträge_aktuelle_ma_stati):
        return STATI['freigegeben']
    
    # Wenn keiner der obigen Fälle: 'In Bearbeitung' bzw. 'Warten auf Vorstufe'
    status_fa = STATI['in_bearbeitung'] if wf_stufe_ist_aktuell(projekt = projekt, wf_stufe = wf_stufe) else STATI['warten_auf_vorstufe']
    return status_fa

def stufenstatus(*, projekt, wf_stufe):
# Ermittelt Status für wf_stufe anhand der Firmenstati
    li_firmen_wf_stufe = hole_objs.liste_prüffirmen_wf_stufe(projekt = projekt, wf_stufe = wf_stufe)

    STATI = {
        'freigegeben': status(projekt = projekt, statusbezeichnung = 'Freigegeben'),
        'abgelehnt': status(projekt = projekt, statusbezeichnung = 'Abgelehnt'),
        'in_bearbeitung': status(projekt = projekt, statusbezeichnung = 'In Bearbeitung'),
        'warten_auf_vorstufe': status(projekt = projekt, statusbezeichnung = 'Warten auf Vorstufe'),
        'rückfrage': status(projekt = projekt, statusbezeichnung = 'Rückfrage')
        }

    status_stufe = STATI['in_bearbeitung'] if wf_stufe_ist_aktuell(projekt = projekt, wf_stufe = wf_stufe) else STATI['warten_auf_vorstufe']
    
    for fa in li_firmen_wf_stufe:
        status_fa = firmenstatus(projekt = projekt, wf_stufe = wf_stufe, prüffirma = fa)

        if status_fa == STATI['abgelehnt']:
            return STATI['abgelehnt']

        if status_fa == STATI['freigegeben'] and status_stufe != STATI['rückfrage']: # Status 'Rückfrage' hemmt die Vergabe eines anderen Status´
            status_stufe = STATI['freigegeben']

        if status_fa == STATI['warten_auf_vorstufe'] and status_stufe != STATI['rückfrage']: # Status 'Rückfrage' hemmt die Vergabe eines anderen Status´
            status_stufe = STATI['warten_auf_vorstufe']

        if status_fa == STATI['in_bearbeitung'] and status_stufe != STATI['rückfrage']: # Status 'Rückfrage' hemmt die Vergabe eines anderen Status´ 
            status_stufe = STATI['in_bearbeitung']

        if status_fa == STATI['rückfrage']:
            status_stufe = STATI['rückfrage']
    
    return status_stufe

def aktualisiere_wf(*, projekt, workflow):
    aktuelle_wf_stufe = hole_objs.aktuelle_wf_stufe(projekt = projekt, workflow = workflow)

    status_aktuelle_stufe = stufenstatus(projekt = projekt, wf_stufe = aktuelle_wf_stufe)

    STATI = {
            'freigegeben': status(projekt = projekt, statusbezeichnung = 'Freigegeben'),
            'abgelehnt': status(projekt = projekt, statusbezeichnung = 'Abgelehnt'),
            'in_bearbeitung': status(projekt = projekt, statusbezeichnung = 'In Bearbeitung'),
            }

    if status_aktuelle_stufe == STATI['abgelehnt']:
        # Neuer Eintrag 'WF_Update_Abgeschlossen' -> True
        neuer_eintrag_wf_update_abgeschlossen = WF_Update_Abgeschlossen(workflow = workflow, abgeschlossen = True, zeitstempel = timezone.now())
        neuer_eintrag_wf_update_abgeschlossen.save(using = str(projekt.id))

    elif status_aktuelle_stufe == STATI['freigegeben']:
        # Aktuelle Stufe schließen
        # Neuer Eintrag 'WF_Stufe_Update_Aktuell' --> False
        aktuelle_wf_stufe_update_aktuell = WF_Stufe_Update_Aktuell(
            workflow_stufe = aktuelle_wf_stufe, 
            aktuell = False, 
            zeitstempel = timezone.now()
            )
        aktuelle_wf_stufe_update_aktuell.save(using = str(projekt.id))

        # Nächste Stufe eröffnen, wenn vorhanden
        nächste_stufe = nächste_wf_stufe(projekt = projekt, wf_stufe = aktuelle_wf_stufe)
        if nächste_stufe:
            # Neuer Eintrag 'WF_Stufe_Update_Aktuell' --> True
            nächste_stufe_update_aktuell = WF_Stufe_Update_Aktuell(
                workflow_stufe = nächste_stufe, 
                aktuell = True, 
                zeitstempel = timezone.now()
                )
            nächste_stufe_update_aktuell.save(using = str(projekt.id))
            
            # Update Prüferstati
            qs_einträge_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(workflow_stufe = nächste_stufe)
            for eintrag in qs_einträge_ma_stufe_status:
                # Neuer Eintrag 'MA_Stufe_Status_Update_Status'
                update_status = MA_Stufe_Status_Update_Status(
                    ma_stufe_status = eintrag,
                    status = STATI['in_bearbeitung'],
                    zeitstempel = timezone.now()
                )
                update_status.save(using = str(projekt.id))
        
        # WF abschließen und Dokument freigeben wenn keine nächste Stufe vorhanden
        else:
            # Neuer Eintrag 'WF_Update_Abgeschlossen' -> True
            neuer_eintrag_wf_update_abgeschlossen = WF_Update_Abgeschlossen(workflow = workflow, abgeschlossen = True, zeitstempel = timezone.now())
            neuer_eintrag_wf_update_abgeschlossen.save(using = str(projekt.id))
            
            # Dokument freigeben
            workflow.dokument.freigegeben = True
            workflow.dokument.save(using = str(projekt.id))
            
            # TODO: InfoMails

def user_ist_stufenprüfer(request, *, projekt, wf_stufe):
# Gibt boole zurück, ob user als Prüfer in der wf_stufe eingetragen ist
    qs_einträge_wf_stufe = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(
        workflow_stufe = wf_stufe,
        mitarbeiter_id = request.user.id
        )

    # User ist Stufenprüfer wenn qs_einträge_wf_stufe nicht leer 
    ist_stufenprüfer = True if qs_einträge_wf_stufe else False
    return ist_stufenprüfer
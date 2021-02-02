from funktionen import hole_objs
from projektadmin.models import WFSch_Stufe_Firma, WFSch_Stufe_Mitarbeiter, Workflow_Schema_Stufe
from superadmin.models import Firma
from dokab.models import Mitarbeiter_Stufe_Status, Workflow_Stufe, Workflow, Status, Dokumentenhistorie_Eintrag, Ereignis, Firma_Stufe
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
            status = Status.objects.using(str(projekt.id)).get(bezeichnung = 'In Bearbeitung'),
            abgeschlossen = False
        )
        neuer_wf.save(using = str(projekt.id))

        # DokHist Eintrag Neuer Workflow
        dokhist_eintrag_neu = Dokumentenhistorie_Eintrag(
            text = 'Neuer Workflow. Dokument: ' + dokument.bezeichnung,
            zeitstempel = timezone.now(),
            dokument = dokument,
            ereignis = Ereignis.objects.using(str(projekt.id)).get(bezeichnung = 'Upload'),
            )
        dokhist_eintrag_neu.save(using = str(projekt.id))

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
                aktuell = True if vorst == None else False,
                bezeichnung = wfsch_st.bezeichnung
                )
            neue_wf_stufe.save(using = str(projekt.id))

            # Prüffirmen verbinden
            qs_einträge_prüffirmen_wfschst = WFSch_Stufe_Firma.objects.using(str(projekt.id)).filter(workflow_schema_stufe = wfsch_st)
            for eintrag_fa in qs_einträge_prüffirmen_wfschst:
                neuer_eintrag_prüffirma_wfst = Firma_Stufe(
                    firma_id = eintrag_fa.firma_id,
                    workflow_stufe = neue_wf_stufe
                )
                neuer_eintrag_prüffirma_wfst.save(using = str(projekt.id))
            
            # Prüfer verbinden
            qs_einträge_prüfer_wfschst = WFSch_Stufe_Mitarbeiter.objects.using(str(projekt.id)).filter(wfsch_stufe = wfsch_st)
            statusbezeichnung = 'In Bearbeitung' if vorst == None else 'Warten auf Vorstufe'
            for eintrag_ma in qs_einträge_prüfer_wfschst:
                neuer_eintrag_prüfer_wfst = Mitarbeiter_Stufe_Status(
                    mitarbeiter_id = eintrag_ma.mitarbeiter_id,
                    workflow_stufe = neue_wf_stufe,
                    status = Status.objects.using(str(projekt.id)).get(bezeichnung = statusbezeichnung),
                    immer_erforderlich = eintrag_ma.immer_erforderlich
                )
                neuer_eintrag_prüfer_wfst.save(using = str(projekt.id))

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

def ereignis(*, projekt, bezeichnung):
# Gibt das Ereignis mit 'bezeichnung' zurück
    return Ereignis.objects.using(str(projekt.id)).get_or_create(bezeichnung = bezeichnung)[0] # Index wegen get_or_create

def firmenstatus(*, projekt, wf_stufe, prüffirma):
# Gibt den Status der Prüffirma zurück
    liste_ma = hole_objs.liste_projektmitarbeiter_firma(projekt = projekt, firma = prüffirma)
    
    liste_einträge_ma_stufe_status = []
    for ma in liste_ma:
        try:
            neuer_eintrag = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).get( # Abfrage mittels filter um Fehlermeldung fehlende
                mitarbeiter_id = ma.id,
                workflow_stufe = wf_stufe,
                gelöscht = False)
        except ObjectDoesNotExist:
            neuer_eintrag = None

        liste_einträge_ma_stufe_status.append(neuer_eintrag)
    
    STATI = {
        'freigegeben': status(projekt = projekt, statusbezeichnung = 'Freigegeben'),
        'abgelehnt': status(projekt = projekt, statusbezeichnung = 'Abgelehnt'),
        'in_bearbeitung': status(projekt = projekt, statusbezeichnung = 'In Bearbeitung'),
        'warten_auf_vorstufe': status(projekt = projekt, statusbezeichnung = 'Warten auf Vorstufe'),
        'rückfrage': status(projekt = projekt, statusbezeichnung = 'Rückfrage')
        }

    status_fa = STATI['in_bearbeitung'] if wf_stufe.aktuell else STATI['warten_auf_vorstufe']
    for s in liste_einträge_ma_stufe_status:
        if s:
            if s.status == STATI['abgelehnt']:
                return STATI['abgelehnt']
            
            if s.status == STATI['freigegeben']:
                status_fa = STATI['freigegeben']

            # Wenn Freigabe von erforderlichem Prüfer fehlt, darf Firmenstatus nicht "freigegeben" bleiben
            if s.immer_erforderlich and s.status != STATI['freigegeben']:
                status_fa = STATI['in_bearbeitung'] if wf_stufe.aktuell else STATI['warten_auf_vorstufe']

            if s.status == STATI['rückfrage']:
                status_fa = STATI['rückfrage']

    return status_fa

def stufenstatus(*, projekt, wf_stufe):
    qs_einträge_firma_stufe = Firma_Stufe.objects.using(str(projekt.id)).filter(workflow_stufe = wf_stufe)
    
    STATI = {
        'freigegeben': status(projekt = projekt, statusbezeichnung = 'Freigegeben'),
        'abgelehnt': status(projekt = projekt, statusbezeichnung = 'Abgelehnt'),
        'in_bearbeitung': status(projekt = projekt, statusbezeichnung = 'In Bearbeitung'),
        'warten_auf_vorstufe': status(projekt = projekt, statusbezeichnung = 'Warten auf Vorstufe'),
        'rückfrage': status(projekt = projekt, statusbezeichnung = 'Rückfrage')
        }

    status_stufe = STATI['in_bearbeitung'] if wf_stufe.aktuell else STATI['warten_auf_vorstufe']
    
    for eintrag in qs_einträge_firma_stufe:
        firma = Firma.objects.using('default').get(pk = eintrag.firma_id)
        status_fa = firmenstatus(projekt = projekt, wf_stufe = wf_stufe, prüffirma = firma)

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

def aktualisiere_wf_status(*, projekt, workflow):
    aktuelle_wf_stufe = Workflow_Stufe.objects.using(str(projekt.id)).get(workflow = workflow, aktuell = True)

    status_aktuelle_stufe = stufenstatus(projekt = projekt, wf_stufe = aktuelle_wf_stufe)

    STATI = {
            'freigegeben': status(projekt = projekt, statusbezeichnung = 'Freigegeben'),
            'abgelehnt': status(projekt = projekt, statusbezeichnung = 'Abgelehnt'),
            'in_bearbeitung': status(projekt = projekt, statusbezeichnung = 'In Bearbeitung'),
            'warten_auf_vorstufe': status(projekt = projekt, statusbezeichnung = 'Warten auf Vorstufe'),
            'rückfrage': status(projekt = projekt, statusbezeichnung = 'Rückfrage')
            }

    if status_aktuelle_stufe == STATI['abgelehnt']:
        workflow.status = STATI['abgelehnt']
        workflow.abgeschlossen = True
        workflow.save(using = str(projekt.id))

    elif status_aktuelle_stufe == STATI['in_bearbeitung'] or status_aktuelle_stufe == STATI['warten_auf_vorstufe'] or status_aktuelle_stufe == STATI['rückfrage']:
        workflow.status = status_aktuelle_stufe
        workflow.save(using = str(projekt.id))

    elif status_aktuelle_stufe == STATI['freigegeben']:
        aktuelle_wf_stufe.aktuell = False
        aktuelle_wf_stufe.save(using = str(projekt.id))
        neuer_dokhist_eintrag_abgeschl = Dokumentenhistorie_Eintrag(
                text = 'Workflowstufe abeschlossen: ' + aktuelle_wf_stufe.bezeichnung,
                zeitstempel = timezone.now(),
                dokument = workflow.dokument,
                ereignis = ereignis(projekt = projekt, bezeichnung = 'Workflow')
            )
        neuer_dokhist_eintrag_abgeschl.save(using = str(projekt.id))

        nächste_stufe = nächste_wf_stufe(projekt = projekt, wf_stufe = aktuelle_wf_stufe)
        if nächste_stufe:
            
            nächste_stufe.aktuell = True
            nächste_stufe.status = STATI['in_bearbeitung']
            nächste_stufe.save(using = str(projekt.id))

            qs_einträge_ma_stufe_status = Mitarbeiter_Stufe_Status.objects.using(str(projekt.id)).filter(workflow_stufe = nächste_stufe)
            for eintrag in qs_einträge_ma_stufe_status:
                eintrag.status = STATI['in_bearbeitung']
                eintrag.save(using = str(projekt.id))

            neuer_dokhist_eintrag_eröffnet = Dokumentenhistorie_Eintrag(
                text = 'Workflowstufe eröffnet: ' + aktuelle_wf_stufe.bezeichnung,
                zeitstempel = timezone.now(),
                dokument = workflow.dokument,
                ereignis = ereignis(projekt = projekt, bezeichnung = 'Workflow')
            )
            neuer_dokhist_eintrag_eröffnet.save(using = str(projekt.id))

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
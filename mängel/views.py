from projektadmin.models import V_PJS_Bezeichnung
from django.shortcuts import render
from django.utils import timezone

from .models import Ticket, Plan, Ticket_Ausstellerstatus, Ticket_Empfängerfirma_Status, Ticket_Plan
from superadmin.models import Projekt
from projektadmin.models import Status, DICT_STATI
from gernotbau.settings import DB_SUPER

# Create your views here.
def ticket_ausstellen_view(request, projekt_id):
    # TODO: Kontrolle Login

    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)

    # POST:
    if request.method == 'POST':
        # EREIGNIS TICKET ERSTELLEN
        if request.POST['ereignis'] == 'ticket_erstellen':
            # Ticket anlegen
            neues_ticket = Ticket.objects.using(pj.db_bezeichnung()).create(
                aussteller_id = request.user.id,
                zeitstempel = timezone.now()
                )
            neues_ticket._entlöschen(pj)
            # Verbindung zu Plan u. Koordinaten
            plan = Plan.objects.using(pj.db_bezeichnung()).get(pk = request.POST['plan_id'])
            Ticket_Plan.objects.using(pj.db_bezeichnung()).create(
                ticket = neues_ticket,
                plan = plan,
                zeitstempel = timezone.now()
                )
            # Ticket-Eigenschaften befüllen
            neues_ticket._x_koordinate_ändern(pj, plan, request.POST['x_koordinate'])
            neues_ticket._y_koordinate_ändern(pj, plan, request.POST['y_koordinate'])
            neues_ticket._bezeichnung_ändern(pj, bezeichnung_neu = request.POST['bezeichnung'])
            neues_ticket._fälligkeitsdatum_ändern(pj, fälligkeitsdatum_neu = request.POST['fälligkeitsdatum'])
            # Empfängerfirma und Status initiieren
            ti_empf = neues_ticket._empfängerfirma_hinzufügen(pj, request.POST.getlist('empfängerfirma_id'))
            status_ib = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'In Bearbeitung')[0]
            Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).create(
                ticket_empfängerfirma = ti_empf,
                status = status_ib,
                zeitstempel = timezone.now()
                )
            # Ausstellerstatus initiieren
            status_war = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Warten auf Rückmeldung')[0]
            Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                ticket = neues_ticket,
                status = status_war,
                zeitstempel = timezone.now()
                )

def übersicht_eingang_view(request, projekt_id):
    # TODO: Kontrolle Login

    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    
    li_tickets_dict = []
    for ti in Ticket.objects.using(pj.db_bezeichnung()).all():
        if ti._empfängerfirma(pj) == request.user.firma and not ti._gelöscht(pj):
            li_tickets_dict.append(ti._dict_für_übersicht(pj))

    # Packe Context und Lade Template:
    context = {
        'liste_tickets': li_tickets_dict,
        'projekt': pj
        }

    return render(request, './mängel/übersicht_eingang.html', context)
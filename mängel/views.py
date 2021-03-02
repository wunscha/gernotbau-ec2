import io
from os import path

from projektadmin.models import V_PJS_Bezeichnung
from django.shortcuts import render
from django.utils import timezone
from gernotbau.settings import MEDIA_ROOT

from .models import Pfad_Plaene, Ticket, Plan, Ticket_Ausstellerstatus, Ticket_Empfängerfirma_Status, Ticket_Plan
from superadmin.models import Projekt, Firma
from projektadmin.models import Status, Pfad_Projekt, Datei, DICT_STATI
from gernotbau.settings import DB_SUPER

# Create your views here.
def ticket_ausstellen_view(request, projekt_id):
    # TODO: Kontrolle Login

    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)

    # POST:
    if request.method == 'POST':
        # EREIGNIS TICKET AUSSTELLEN
        if request.POST['ereignis'] == 'ticket_ausstellen':
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
            ti_empf = neues_ticket._empfängerfirma_ändern(pj, request.POST['empfängerfirma_id'])
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

    # Packe Context und lade Template
    li_pläne_dict = []
    for p in Plan.objects.using(pj.db_bezeichnung()).all():
        if not p._gelöscht(pj):
            dict_p = p.__dict__
            dict_p['bezeichnung'] = p._bezeichnung(pj)
            li_pläne_dict.append(dict_p)

    li_projektfirmen_dict = []
    for f in pj.liste_projektfirmen():
        dict_firma = f.__dict__
        dict_firma['bezeichnung'] = f._bezeichnung()
        li_projektfirmen_dict.append(dict_firma)

    context = {
        'liste_pläne': li_pläne_dict,
        'liste_projektfirmen': li_projektfirmen_dict,
        'projekt': pj
        }

    return render(request, './mängel/ticket_ausstellen.html', context)

def übersicht_tickets_view(request, projekt_id):
    # TODO: Kontrolle Login

    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    li_tickets_dict = []

    # Alle ungelöschten Tickets anzeigen
    for ti in Ticket.objects.using(pj.db_bezeichnung()).all():
        if not ti._gelöscht(pj):
            li_tickets_dict.append(ti._dict_für_übersicht(pj))

    # Packe Context und lade Template
    context = {
        'liste_tickets': li_tickets_dict,
        'projekt': pj
        }

    return render(request, './mängel/übersicht_tickets.html', context)

def übersicht_pläne_view(request, projekt_id):
    # TODO: Kontrolle Login
    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)

    # Packe Context und lade Template
    li_pläne_dict = []

    for p in Plan.objects.using(pj.db_bezeichnung()).all():
        if not p._gelöscht(pj):
            dict_p = p.__dict__
            dict_p['bezeichnung'] = p._bezeichnung(pj)
            li_pläne_dict.append(dict_p)

    context = {
        'liste_pläne': li_pläne_dict,
        'projekt': pj
        }

    return render(request, './mängel/übersicht_pläne.html', context)

def plan_anlegen_view(request, projekt_id):
    # TODO: Kontrolle Login
    
    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)

    # POST
    if request.method == 'POST':
        pfad_projekt = Pfad_Projekt.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
        pfad_pläne = Pfad_Plaene.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
        # EREIGNIS Plan hochladen:
        if request.POST['ereignis'] == 'plan_anlegen':
            # Datei hochladen
            upload_datei = request.FILES['datei']
            zielpfad = path.join(str(MEDIA_ROOT), pfad_projekt, pfad_pläne, upload_datei.name)
            with open(zielpfad, 'wb+') as ziel:
                for chunk in request.FILES['datei'].chunks():
                    ziel.write(chunk)
                ziel.close()
            # Plan in DB anlegen
            neue_datei = Datei.objects.using(pj.db_bezeichnung()).create(
                dateiname = upload_datei.name,
                zeitstempel = timezone.now()
                )
            neuer_plan = Plan.objects.using(pj.db_bezeichnung()).create(
                breite = 100, # TODO: Breite von Dateieigenschaften übernehmen
                hoehe = 100, # TODO: Höhe von Dateieigenschaften übernehmen
                datei = neue_datei
                )
            neuer_plan._entlöschen(pj)
            neuer_plan._bezeichnung_ändern(pj, neue_bezeichnung = request.POST['bezeichnung'])

    # Packe Context und Lade Template
    context = {
        'projekt': pj
        }
    
    return render(request, './mängel/plan_anlegen.html', context)
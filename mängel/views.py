import io
from os import path

from projektadmin.models import V_PJS_Bezeichnung
from django.shortcuts import render
from django.utils import timezone
from gernotbau.settings import MEDIA_ROOT, MEDIA_URL, STATIC_URL
from django.contrib.auth import get_user_model

from .models import Pfad_Plaene, Ticket, Plan, Ticket_Ausstellerstatus, Ticket_Empfängerfirma, Ticket_Empfängerfirma_Status, Ticket_Plan, Ticket_Kommentar, Ticket_Kommentar_Anhang
from superadmin.models import Projekt, Firma
from projektadmin.models import Status, Pfad_Projekt, Pfad_Anhaenge, Datei, DICT_STATI
from gernotbau.settings import DB_SUPER, STATICFILES_DIRS

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

def übersicht_tickets_plan_view(request, projekt_id, plan_id):
    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    plan = Plan.objects.using(pj.db_bezeichnung()).get(pk = plan_id)

    # Hole alle ungelöschten Ticket für plan
    qs_ti_plan = Ticket_Plan.objects.using(pj.db_bezeichnung()).filter(plan = plan)
    li_tickets_dict = []
    for ti_plan in qs_ti_plan:
        ticket = ti_plan.ticket
        if not ticket._gelöscht(pj):
            ticket_dict = ticket._dict_für_übersicht(pj)
            ticket_dict['x_koordinate'] = float(ticket._x_koordinate(pj, plan))
            ticket_dict['y_koordinate'] = float(ticket._y_koordinate(pj, plan))
            ticket_dict['historie'] = ticket._historie(pj)
            li_tickets_dict.append(ticket_dict)

    # Plan
    plan_dict = plan.__dict__
    plan_dict['bezeichnung'] = plan._bezeichnung(pj)
    pfad_projekt = Pfad_Projekt.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
    pfad_plaene = Pfad_Plaene.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
    plan_dict['pfad'] = str(path.join(STATIC_URL, pfad_projekt, pfad_plaene, plan.datei.dateiname))

    # Packe Context und lade Template
    context = {
        'projekt': pj,
        'plan': plan_dict,
        'liste_tickets': li_tickets_dict
        }

    return render(request, './mängel/übersicht_tickets_plan.html', context)

def detailansicht_ticket_view(request, projekt_id, ticket_id):
    # TODO: Kontrolle Login

    pj = Projekt.objects.using(DB_SUPER).get(pk = projekt_id)
    ti = Ticket.objects.using(pj.db_bezeichnung()).get(pk = ticket_id)

    # Ticket als gelesen Markieren, wenn user von Empfängerfirma
    if str(request.user.firma.id) == str(ti._empfängerfirma(pj).id):
        ti._empfängerfirma_gelesen_markieren(pj)
    
    # POST
    if request.method == 'POST':
        # AUSSTELLERSTATI
        if request.POST['ereignis'] == 'ausstellerstatus_freigegeben':
            status_fg = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Freigegeben')[0]
            Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                ticket = ti,
                status = status_fg,
                zeitstempel = timezone.now()
                )
            # TODO: Infomail

        if request.POST['ereignis'] == 'ausstellerstatus_abgelehnt':
            status_ab = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Abgelehnt')[0]
            Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                ticket = ti,
                status = status_ab,
                zeitstempel = timezone.now()
                )
            # TODO: Popup -> Eingabe Ablehnungsgrund (Speicherung als Kommentar + Nachricht)

        if request.POST['ereignis'] == 'ausstellerstatus_nachbesserung':
            # Ausstellerstatus
            status_nb = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Nachbesserung')[0]
            Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                ticket = ti,
                status = status_nb,
                zeitstempel = timezone.now()
                )
            # TODO: Popup -> Eingabe Infos Nachbesserung (Speicherung als Kommentar + Nachricht)
            # Empfängerstatus
            status_ib = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'In Bearbeitung')[0]
            ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = ti).latest('zeitstempel')
            Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).create(
                ticket_empfängerfirma = ti_empf,
                status = status_ib,
                zeitstempel = timezone.now()
                )

        if request.POST['ereignis'] == 'ausstellerstatus_zurückgezogen':
            status_zgz = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Zurückgezogen')[0]
            Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                ticket = ti,
                status = status_zgz,
                zeitstempel = timezone.now()
                )

        # EMPFÄNGERSTATI
        if request.POST['ereignis'] == 'empfängerstatus_behoben':
            # Empfängerstatus
            status_beh = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Behoben')[0]
            ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = ti).latest('zeitstempel')
            Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).create(
                ticket_empfängerfirma = ti_empf,
                status = status_beh,
                zeitstempel = timezone.now()
                )
            # TODO: Popup --> Möglichkeit Kommentar/Fotos anzuhängen
            status_ib = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'In Bearbeitung')[0]
            Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                ticket = ti,
                status = status_ib,
                zeitstempel = timezone.now()
                )

        if request.POST['ereignis'] == 'empfängerstatus_zurückgewiesen':
            # Empfängerstatus --> Zurückgewiesen
            status_zgw = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Zurückgewiesen')[0]
            ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = ti).latest('zeitstempel')
            Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).create(
                ticket_empfängerfirma = ti_empf,
                status = status_zgw,
                zeitstempel = timezone.now()
                )
            # TODO: Popup --> Eingabe Zurückweisungsgrund (Speicherung als Kommentar + Nachricht)

        # KOMMENTAR
        if request.POST['ereignis'] == 'kommentar':
            # Kommentar anlegen
            neues_kommentar = Ticket_Kommentar.objects.using(pj.db_bezeichnung()).create(
                ticket = ti,
                mitarbeiter_id = request.user.id,
                text = request.POST['text'],
                zeitstempel = timezone.now()
                )
            
            # Anhänge hochladen
            pfad_projekt = Pfad_Projekt.objects.using(pj.db_bezeichnung()).latest('zeitstempel')
            pfad_anhänge = Pfad_Anhaenge.objects.using(pj.db_bezeichnung()).latest('zeitstempel')
            zielordner = path.join(STATICFILES_DIRS, pfad_projekt.pfad, pfad_anhänge.pfad) # TODO: Pfad anpassen ('STATIFILES_DIRS' nur für Produktion)
            for f in request.FILES.getlist('anhänge'):
                # Datein in DB anlegen
                neue_datei = Datei.objects.using(pj.db_bezeichnung()).create(
                    dateiname = f.name,
                    zeitstempel = timezone.now()
                    )
                # Hochladen
                zielpfad = path.join(zielordner, f'{neue_datei.id}_{neue_datei.dateiname}')
                with open(zielpfad, 'wb+') as ziel:
                    for chunk in f.chunks():
                        ziel.write(chunk)
                    ziel.close()
                # Verbindung Ticket-Kommentar-Anhang
                Ticket_Kommentar_Anhang.objects.using(pj.db_bezeichnung()).create(
                    ticket_kommentar = neues_kommentar,
                    datei = neue_datei,
                    zeitstempel = timezone.now()
                    )

        # TICKET ÄNDERN
        if request.POST['ereignis'] == 'ticket_aktualisieren':
            # Bezeichnung Ändern
            if str(ti._bezeichnung(pj)) != str(request.POST['bezeichnung']):
                ti._bezeichnung_ändern(pj, bezeichnung_neu = request.POST['bezeichnung'])
            # Koordinaten Ändern
            plan = ti._plan(pj)
            if str(ti._x_koordinate(pj, plan)) != str(request.POST['x_koordinate']):
                ti._x_koordinate_ändern(pj, plan, x_koordinate_neu = request.POST['x_koordinate'])
            if str(ti._y_koordinate(pj, plan)) != str(request.POST['y_koordinate']):
                ti._y_koordinate_ändern(pj, plan, y_koordinate_neu = request.POST['y_koordinate'])
            # Empfängerfirma Ändern (inkl. Stati zurücksetzen)
            if str(ti._empfängerfirma(pj).id) != str(request.POST['empfängerfirma_id']):
                ti._empfängerfirma_ändern(pj, empfängerfirma_neu_id = request.POST['empfängerfirma_id'])
                # Status Aussteller
                status_war = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'Warten auf Rückmeldung')[0]
                Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).create(
                    ticket = ti,
                    status = status_war,
                    zeitstempel = timezone.now()
                    )
                # Status Empfängerfirma
                status_ib = Status.objects.using(pj.db_bezeichnung()).get_or_create(bezeichnung = 'In Bearbeitung')[0]
                ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = ti).latest('zeitstempel')
                Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).create(
                    ticket_empfängerfirma = ti_empf,
                    status = status_ib,
                    zeitstempel = timezone.now()
                    )

    # Packe Context und lade Template
    User = get_user_model()
    li_kommentare = []
    for k in Ticket_Kommentar.objects.using(pj.db_bezeichnung()).filter(ticket = ti):
        dict_k = k.__dict__
        # Mitarbeiter
        ma = User.objects.using(DB_SUPER).get(pk = k.mitarbeiter_id)
        dict_k['mitarbeiter'] = f'{ma.first_name} {ma.last_name}'
        # Anhänge
        li_anhänge = []
        for a in Ticket_Kommentar_Anhang.objects.using(pj.db_bezeichnung()).filter(ticket_kommentar = k):
            dict_a = a.__dict__
            dict_a['dateiname'] = a.datei.dateiname
            pfad_projekt = Pfad_Projekt.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
            pfad_anhänge = Pfad_Anhaenge.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
            dict_a['dateipfad'] = path.join(pfad_projekt, pfad_anhänge, f'{a.datei.id}_{a.datei.dateiname}') # TODO: Pfad für Produktion ggf anpassen
            li_anhänge.append(dict_a)
        dict_k['liste_anhänge'] = li_anhänge
        
        li_kommentare.append(dict_k)

    li_projektfirmen_dict = []
    for f in pj.liste_projektfirmen():
        dict_firma = f.__dict__
        dict_firma['bezeichnung'] = f._bezeichnung()
        li_projektfirmen_dict.append(dict_firma)

    dict_ticket = ti._dict_für_übersicht(pj)
    dict_ticket['x_koordinate'] = str(ti._x_koordinate(pj, plan = ti._plan(pj)))
    dict_ticket['x_koordinate'].replace(',', '.')
    dict_ticket['y_koordinate'] = str(ti._y_koordinate(pj, plan = ti._plan(pj)))
    dict_ticket['y_koordinate'].replace(',', '.')
    dict_ticket

    context = {
        'ticket': dict_ticket,
        'liste_projektfirmen': li_projektfirmen_dict,
        'liste_historie': ti._historie(pj),
        'user_ist_aussteller': str(request.user.id) == str(ti.aussteller_id),
        'userfirma_ist_empfängerfirma': str(request.user.firma.id) == str(ti._empfängerfirma(pj).id),
        'projekt': pj.__dict__
        }

    return render(request, './mängel/detailansicht_ticket.html', context)

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
            zielpfad = path.join(STATICFILES_DIRS[0], pfad_projekt, pfad_pläne, upload_datei.name)  # TODO: Pfad anpassen ('STATIFILES_DIRS' nur für Produktion)
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

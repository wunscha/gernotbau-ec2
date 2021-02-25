from django.shortcuts import render
from django.utils import timezone

from .models import Nachricht, Nachricht_Empfänger, Nachricht_Empfänger_Gelesen
from superadmin.models import Mitarbeiter
from gernotbau.settings import DB_SUPER

def übersicht_eingang_view(request):
    # TODO: Kontrolle Login
    qs_nr_empf = Nachricht_Empfänger.objects.using(DB_SUPER).filter(empfänger = request.user)

    li_nr_gelesen = []
    li_nr_neu = []
    for nr_empf in qs_nr_empf:
        dict_nr = nr_empf.nachricht.__dict__
        dict_nr['verfasser'] = nr_empf.nachricht.verfasser.__dict__

        if nr_empf._gelesen():
            li_nr_gelesen.append(dict_nr)
        else:
            li_nr_neu.append(dict_nr)

    # Ungelesene Nachrichten
    context = {
        'liste_nachrichten_gelesen': li_nr_gelesen,
        'liste_nachrichten_neu': li_nr_neu,
        }

    return render(request, './kommunikation/übersicht_eingang.html', context)

def übersicht_gesendet_view(request):
    # TODO: Kontrolle Login

    qs_nr = Nachricht.objects.using(DB_SUPER).filter(verfasser = request.user)

    li_nr_gesendet = []
    for nr in qs_nr:
        dict_nr = nr.__dict__
        dict_nr['liste_empfänger'] = nr._liste_empfänger_dict()
        li_nr_gesendet.append(dict_nr)

    context = {'liste_nachrichten': li_nr_gesendet}

    return render(request, './kommunikation/übersicht_gesendet.html', context)

def detailansicht_nachricht_view(request, nachricht_id):
    # TODO: Kontrolle Login
    
    nachricht = Nachricht.objects.using(DB_SUPER).get(pk = nachricht_id)

    # EINTRAG IN 'GELESEN' (außer Verfasser schaut sichs an)
    if not nachricht.verfasser.id == request.user.id:
        nr_empf = Nachricht_Empfänger.objects.using(DB_SUPER).get(
                    nachricht = nachricht,
                    empfänger = request.user,
                    )
        Nachricht_Empfänger_Gelesen.objects.using(DB_SUPER).create(
            nachricht_empfänger = nr_empf,
            zeitstempel = timezone.now()
            )
    
    dict_nr = nachricht.__dict__
    dict_nr['liste_empfänger'] = nachricht._liste_empfänger_dict()
    dict_nr['verfasser'] = nachricht.verfasser.__dict__

    context =  {
        'nachricht': dict_nr
        }

    return render(request, './kommunikation/detailansicht_nachricht.html', context)

def nachricht_verfassen_view(request, empfänger_id):
    # TODO: Kontrolle Login

    if request.method == 'POST':
        # EREIGNIS NACHRICHT SENDEN
        if request.POST['ereignis'] == 'nachricht_senden':
            neue_nachricht = Nachricht.objects.using(DB_SUPER).create(
                verfasser = request.user,
                text = request.POST['text'],
                betreff = request.POST['betreff'],
                zeitstempel = timezone.now()
                )
            
            li_empf_id = request.POST.getlist('empfänger_id')
            for empf_id in li_empf_id:
                empf = Mitarbeiter.objects.using(DB_SUPER).get(pk = empf_id)
                Nachricht_Empfänger.objects.using(DB_SUPER).create(
                    empfänger = empf,
                    nachricht = neue_nachricht,
                    )

    # Packe Context und Lade Template:
    li_ma_dict = []
    for ma in Mitarbeiter.objects.using(DB_SUPER).all():
        if not ma.gelöscht() and not str(ma.id) == empfänger_id:
            ma_dict = ma.__dict__
            ma_dict['bezeichnung_firma'] = ma.firma._bezeichnung()
            li_ma_dict.append(ma)

    if empfänger_id != 'keine_vorauswahl':
        dict_empf_vorauswahl = Mitarbeiter.objects.using(DB_SUPER).get(pk = empfänger_id).__dict__
    else:
        dict_empf_vorauswahl = None

    context = {
        'liste_mitarbeiter': li_ma_dict,
        'empfänger_vorauswahl': dict_empf_vorauswahl,
        }

    return render(request, './kommunikation/nachricht_verfassen.html', context)
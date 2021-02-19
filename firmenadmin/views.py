from gernotbau.settings import DB_SUPER
from django.shortcuts import render
from django.contrib.auth import get_user_model
from superadmin.models import Mitarbeiter, Projekt, Firma
from projektadmin.models import Rolle, Workflow_Schema, WFSch_Stufe, WFSch_Stufe_Rolle, WFSch_Stufe_Firma, WFSch_Stufe_Mitarbeiter, firma_liste_wfsch_dict, liste_rollen_firma_dict, liste_rollen_mitarbeiter, liste_rollen_mitarbeiter_dict, liste_projekte_mitarbeiter_dict, firma_liste_mitarbeiter_projekt_dict
from django.http import HttpResponse, HttpResponseRedirect
from .forms import MitarbeiterNeuForm
from django.urls import reverse
from funktionen import hole_dicts, emailfunktionen
from django.contrib.auth.hashers import make_password

# MITARBEITER

def übersicht_mitarbeiter_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin

    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    # POST
    if request.method == 'POST':
        # EREIGNIS MITARBEITER LÖSCHEN
        if request.POST['ereignis'] == 'mitarbeiter_löschen':
            User = get_user_model()
            User.objects.using(DB_SUPER).get(pk = request.POST['mitarbeiter_id']).löschen()

    User = get_user_model()
    li_ma_dict = firma.liste_mitarbeiter_dict()
    for ma_dict in li_ma_dict:
        ma = User.objects.using(DB_SUPER).get(pk = ma_dict['id'])
        ma_dict['liste_projekte'] = liste_projekte_mitarbeiter_dict(ma)

    context = {
        'firma': firma.firma_dict(),
        'liste_mitarbeiter': li_ma_dict,
        }
    return render(request, './firmenadmin/übersicht_mitarbeiter.html', context)

def detailansicht_mitarbeiter_view(request, firma_id, mitarbeiter_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)
    User = get_user_model()
    mitarbeiter = User.objects.using(DB_SUPER).get(pk = mitarbeiter_id)



    # Packe context und lade Template:
    li_pj_dict = mitarbeiter.liste_projekte_dict()
    for pj_dict in li_pj_dict:
        projekt = Projekt.objects.using(DB_SUPER).get(pk = pj_dict.id)
        pj_dict['liste_rollen'] = liste_rollen_mitarbeiter_dict(projekt, mitarbeiter)

    context = {
        'firma': firma.firma_dict(),
        'mitarbeiter': mitarbeiter.mitarbeiter_dict()
        }

def mitarbeiter_anlegen_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin
    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    # POST
    if request.method == 'POST':
        # EREIGNIS MITARBEITER ANLEGEN
        if request.POST['ereignis'] == 'mitarbeiter_anlegen':
            firma.mitarbeiter_anlegen(formulardaten = request.POST)

    # Packe Context und Lade Template
    context = {
        'firma': firma,
        }
    return render(request, './firmenadmin/mitarbeiter_anlegen.html', context)

# PROJEKTE

def übersicht_projekte_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin

    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)

    # POST
    if request.method == 'POST':

        # EREIGNIS ROLLENINHABER HINZUFÜGEN
        if request.POST['ereignis'] == 'rolleninhaber_hinzufügen':
            projekt = Projekt.objects.using(DB_SUPER).get(pk = request.POST['projekt_id'])
            rolle = Rolle.objects.using(projekt.db_bezeichnung()).get(pk = request.POST['rolle_id'])
            User = get_user_model()
            mitarbeiter = User.objects.using(DB_SUPER).get(pk = request.POST['mitarbeiter_id'])
            rolle.rolleninhaber_hinzufügen(projekt, mitarbeiter)

        # EREIGNIS ROLLENINHABER LÖSEN
        if request.POST['ereignis'] == 'rolleninhaber_lösen':
            projekt = Projekt.objects.using(DB_SUPER).get(pk = request.POST['projekt_id'])
            rolle = Rolle.objects.using(projekt.db_bezeichnung()).get(pk = request.POST['rolle_id'])
            User = get_user_model()
            mitarbeiter = User.objects.using(DB_SUPER).get(pk = request.POST['mitarbeiter_id'])
            rolle.rolleninhaber_lösen(projekt, mitarbeiter)

    # Packe Context und lade Template
    li_projekte_dicts = []
    for projekt in firma.liste_projekte():
        dict_projekt = projekt.projekt_dict()
        dict_projekt['liste_rollen'] = liste_rollen_firma_dict(projekt, firma)
        dict_projekt['liste_projektmitarbeiter'] = firma_liste_mitarbeiter_projekt_dict(projekt, firma)
        dict_projekt['firma_ist_projektadmin'] = firma.ist_projektadmin(projekt)
        li_projekte_dicts.append(dict_projekt)

    context = {
        'firma': firma,
        'liste_projekte': li_projekte_dicts, 
        }
    
    return render(request, './firmenadmin/übersicht_projekte.html', context)

# WFSCH

def übersicht_wfsch_view(request, firma_id):
    # TODO: Kontrolle Login
    # TODO: Kontrolle Firmenadmin

    firma = Firma.objects.using(DB_SUPER).get(pk = firma_id)
    
    # POST
    if request.method == 'POST':
        
        # OBJEKTE HOLEN
        pj = Projekt.objects.using(DB_SUPER).get(pk = request.POST['projekt_id'])
        
        if request.POST['ereignis'] == 'firmenprüfer_hinzufügen' or request.POST['ereignis'] == 'firmenprüfer_lösen':
            wfschSt = WFSch_Stufe.objects.using(pj.db_bezeichnung()).get(pk = request.POST['wfsch_stufe_id'])
            ma = Mitarbeiter.objects.using(DB_SUPER).get(pk = request.POST['mitarbeiter_id'])
            ro = Rolle.objects.using(pj.db_bezeichnung()).get(pk = request.POST['rolle_id'])
            wfschSt_ro = WFSch_Stufe_Rolle.objects.using(pj.db_bezeichnung()).get(wfsch_stufe = wfschSt, rolle = ro)
            wfschSt_fa = WFSch_Stufe_Firma.objects.using(pj.db_bezeichnung()).get(wfsch_stufe_rolle = wfschSt_ro, firma_id = ma.firma.id)
        
        # EREIGNIS FIRMENPRÜFER HINZUFÜGEN
        if request.POST['ereignis'] == 'firmenprüfer_hinzufügen':
            wfschSt_fa.firmenprüfer_hinzufügen(projekt = pj, firmenprüfer_neu = ma)

        # EREIGNIS FIRMENPRÜFER LÖSEN
        if request.POST['ereignis'] == 'firmenprüfer_lösen':
            wfschSt_fa.firmenprüfer_lösen(projekt = pj, firmenprüfer_lö = ma)

        # EREIGNIS MITARBEITER NACH ROLLEN ZUWEISEN
        if request.POST['ereignis'] == 'mitarbeiter_nach_rollen_zuweisen':
            wfschSt = Workflow_Schema.objects.using(pj.db_bezeichnung()).get(pk = request.POST['wfsch_id'])
            wfschSt.firmenprüfer_nach_rollen_zuweisen(pj, firma)

    # Packe context und lade Template
    li_wfsch_dict = []
    for pj in firma.liste_projekte():
        dict_pj = pj.projekt_dict()
        dict_pj['liste_wfsch'] = firma_liste_wfsch_dict(pj, firma)
        li_wfsch_dict.append(dict_pj)
    
    context = {
        'firma': firma,
        'liste_wfsch_firma': li_wfsch_dict,
        }

    return render(request, './firmenadmin/übersicht_wfsch.html', context)

from django.shortcuts import render
from django.contrib.auth import get_user_model
from superadmin.models import Mitarbeiter, Projekt_Mitarbeiter_Mail, Projekt_Firma_Mail, Projekt
from projektadmin.models import Workflow_Schema_Stufe, WFSch_Stufe_Mitarbeiter
from django.http import HttpResponse, HttpResponseRedirect
from .forms import MitarbeiterNeuForm
from django.urls import reverse
from funktionen import hole_dicts, emailfunktionen
from django.contrib.auth.hashers import make_password

def übersicht_mitarbeiter_view(request):

    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')

    else:
        #Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)
        else:
            # POST: Ereignis Abfragen (= Vorarbeit für etwaige Erweiterungen):
            if request.method == 'POST':
                if request.POST['ereignis'] == 'mitarbeiter_löschen':
                    löschkandidat = Mitarbeiter.objects.using('default').get(pk = request.POST['mitarbeiter_löschen_id'])
                    löschkandidat.aktiv = False
                    löschkandidat.save(using = 'default')

                    # TODO: InfoMail
                    # TODO: Verknüpfungen löschen

            liste_mitarbeiter = hole_dicts.firmenmitarbeiter(firma = request.user.firma)
            context = {'liste_mitarbeiter': liste_mitarbeiter}
            return render(request, './firmenadmin/übersicht_mitarbeiter.html', context)
    
def mitarbeiter_neu_view(request):

    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './registration/login.html', context)

        else:
            # POST: Neuen Mitarbeiter anlegen
            neuer_mitarbeiter = None # Vorbereitung für context
            if request.method == 'POST':
                
                # E-Mail-Adresse generieren (inkl. Kontrolle ob Adresse schon vorhanden)
                email = emailfunktionen.generiere_email_adresse_ma(
                    firma = request.user.firma, 
                    nachname = request.POST['nachname']
                    )

                User = get_user_model()
                neuer_mitarbeiter = User(
                    first_name = request.POST['vorname'],
                    last_name = request.POST['nachname'],
                    password = make_password(request.POST['passwort']), # Erzeugt gehashtes Passwort
                    firma = request.user.firma,
                    email = email,
                    username = email,
                    ist_firmenadmin = False, 
                    ist_superadmin = False
                )

                neuer_mitarbeiter.save(using = 'default')

            # context packen und Bestätigungsseite laden
            dict_neuer_mitarbeiter = neuer_mitarbeiter.__dict__ if neuer_mitarbeiter else None
            
            context = {'neuer_mitarbeiter': dict_neuer_mitarbeiter}
            return render(request, './firmenadmin/mitarbeiter_neu.html', context)

def übersicht_projekte_view(request):

    # Prüfung Login:
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    else:

        # Prüfung Firmenadmin:
        if not request.user.ist_firmenadmin:
            fehlermeldung = 'Bitte loggen Sie sich als Firmenadmin für die gewünschte Firma ein'
            context = {'fehlermeldung': fehlermeldung}
            return render(request, './firmenadmin/übersicht_projekte.html', context)
        else:
            if request.method == 'POST':
                # Mitarbeiter zu Projekt hinzufügen
                if request.POST['ereignis'] == 'mitarbeiter_hinzufügen':
                    pass
                
                # Mitarbeiter von Projekt lösen
                elif request.POST['ereignis'] == 'mitarbeiter_lösen':
                    pass
            
            # context packen und Übersich laden
            liste_projekte = hole_dicts.projekte_firma(firma = request.user.firma)
            context = {'liste_projekte': liste_projekte}
            
            return render(request, './firmenadmin/übersicht_projekte.html', context)

def mitarbeiter_zu_projekt(request):
# Wenn POST: Mitarbeiter zu Projekt hinzufügen
# Wenn nicht POST passiert nichts

    if request.method == 'POST':
        mitarbeiter_id = request.POST['mitarbeiter']
        User = get_user_model()
        mitarbeiter = User.objects.get(pk = mitarbeiter_id)
        projekt_id = request.POST['projekt_id']
        projekt = Projekt.objects.get(pk = projekt_id)
        email = str('%s.%s.%s@gernotbau.at' % (mitarbeiter.last_name, mitarbeiter.firma.kurzbezeichnung, projekt.kurzbezeichnung))
        pj_ma_mail_neu = Projekt_Mitarbeiter_Mail.objects.create(
            email = email,
            mitarbeiter = mitarbeiter,
            ist_projektadmin = False,
            projekt = projekt
        )

        return HttpResponseRedirect(reverse('firmenadmin:projekte_übersicht'))

def mitarbeiter_als_projektadmin(request):
# Wenn POST: Lege Mitarbeiter als Projektadmin fest
    if request.method == 'POST':
        # Hole Eintrage in Projekt_Mitarbeiter_Mail
        firma = request.user.firma
        projekt_id = request.POST['projekt_id']
        projekt = Projekt.objects.get(pk = projekt_id)
        User = get_user_model()
        mitarbeiter_id = request.POST['mitarbeiter_projektadmin']
        mitarbeiter = User.objects.get(pk = mitarbeiter_id)
        liste_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.filter(mitarbeiter__firma = firma)

        for eintrag in liste_pj_ma_mail:
            # Wenn gewählter Mitarbeiter: Lege als Projektadmin fest
            if eintrag.mitarbeiter == mitarbeiter:
                eintrag.ist_projektadmin = True
                eintrag.save()

            # Sonst: Ist nicht Projektadmin
            else:
                eintrag.ist_projektadmin = False
                eintrag.save()
                
        # Weiterleitung zur Projektübersicht
        return HttpResponseRedirect(reverse('firmenadmin:projekte_übersicht'))

def workflowsÜbersichtView(request):
# Wenn Firmenadmin: Zeige Workflows an, die der Firma zugewiesen wurdne
    if request.user.ist_firmenadmin:
        # Hole alle Workflow-Schema-Stufen, die der Firma zugeordnet wurden
        firma = request.user.firma
        liste_wfsch_stufen = []
        liste_wfsch_stufen_fa = Workflow_Schema_Stufe.objects.filter(prüffirma = firma)
        for wfsch_stufe_fa in liste_wfsch_stufen_fa:
            dict_stufe = {}
            dict_stufe['wfsch_stufe_fa'] = wfsch_stufe_fa
            dict_stufe['wfsch_stufe_id'] = wfsch_stufe_fa.id
            liste_wfsch_stufe_prüfer = WFSch_Stufe_Mitarbeiter.objects.filter(mitarbeiter__firma = firma, wfsch_stufe = wfsch_stufe_fa)
            dict_stufe['liste_wfsch_stufe_prüfer'] = liste_wfsch_stufe_prüfer
            liste_wfsch_stufen.append(dict_stufe)
        
        # Mitarbeiterliste für Dropdown für Mitarbeiter zuweisen
        liste_mitarbeiter = firma.mitarbeiter_set.all()

        context = {
            'liste_wfsch_stufen':liste_wfsch_stufen,
            'liste_mitarbeiter':liste_mitarbeiter
            }

        return render(request, 'workflows_übersicht.html', context)

def wfsch_prüfer_zuordnen(request):
# Wenn POST, dann füge Prüfer zu WFSch-Stufe hinzu, sonst passiert nichts
    if request.method == 'POST':
        prüfer_id = request.POST['prüfer_id']
        User = get_user_model()
        prüfer = User.objects.get(pk = prüfer_id)
        wfsch_stufe_id = request.POST['wfsch_stufe_id']
        wfsch_stufe = Workflow_Schema_Stufe.objects.get(pk = wfsch_stufe_id)
        neuer_eintrag = WFSch_Stufe_Mitarbeiter.objects.create(
            mitarbeiter = prüfer,
            immer_erforderlich = False,
            wfsch_stufe = wfsch_stufe
        )
        
        # TODO: InfoMails
        # TODO: Alle bestehenden Workflows dieses Schemas schließen (Davor Warnhinweis)

        return HttpResponseRedirect(reverse('firmenadmin:workflows_übersicht'))
from django.shortcuts import render
from django.contrib.auth import get_user_model
from superadmin.models import Projekt_Mitarbeiter_Mail, Projekt_Firma_Mail, Projekt
from projektadmin.models import Workflow_Schema_Stufe, WFSch_Stufe_Mitarbeiter
from django.http import HttpResponse, HttpResponseRedirect
from .forms import MitarbeiterNeuForm
from django.urls import reverse

def mitarbeiterÜbersichtView(request):
# Wenn User Firmenadmin ist, dann zeige Auflistung der Mitarbeiter seiner Firma,
# sonst leite weiter auf Zugriff-verweiger-Template

    if request.user.ist_firmenadmin:
        firma = request.user.firma
        MitarbeiterModel = get_user_model()
        liste_mitarbeiter = MitarbeiterModel.objects.filter(firma = firma)
        # Befülle dict_mitarbeiter für context
        dict_mitarbeiter = {}
        for mitarbeiter in liste_mitarbeiter:
            pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.filter(mitarbeiter = mitarbeiter)
            name_mitarbeiter = str('%s %s' % (mitarbeiter.first_name, mitarbeiter.last_name))
            dict_mitarbeiter[name_mitarbeiter] = pj_ma_mail

        # Beffülle context und rendere Template für Mitarbeiter-Übesicht
        context = {'dict_mitarbeiter':dict_mitarbeiter}
        return render(request, 'mitarbeiter_übersicht.html', context)
    
    else:
        return render(request, 'firmenadmin_zugriff_verweigert.html')
    
def mitarbeiterNeuView(request):
# Wenn User Firmenadmin ist:
# Wenn POST dann lege neuen Mitarbeiter an
# Wenn nicht POST dann zeige Formular für neuen Mitarbeiter,
# Wenn User nicht Firmenadmin, dann leite weiter auf Zugriff-verweiger-Template

    if request.user.ist_firmenadmin:
        # Wenn POST: Lege neuen Mitarbeiter aus Formulardaten an
        if request.method == 'POST':
            firma = request.user.firma
            vorname = request.POST['vorname']
            nachname = request.POST['nachname']
            email = request.POST['email']
            passwort = request.POST['passwort']
            username = vorname + '.' + nachname

            User = get_user_model()
            neuer_mitarbeiter = User.objects.create_user(
                first_name = vorname,
                last_name = nachname,
                email = email,
                password = passwort,
                username = username,
                firma = firma,
                ist_firmenadmin = False,
            )

            #TODO: Mehrfacheinträge verhindern
            #TODO: InfoMail

            # Weiterleitung zu Mitarbeiterübersicht
            return HttpResponseRedirect(reverse('firmenadmin:mitarbeiter_übersicht'))
        
        # Wenn nicht POST: Zeige Formular für neuen Mitarbeiter
        else: 
            return render(request,'mitarbeiter_neu_formular.html')

    # Wenn nicht Firmenadmin: Zugriff verweigert
    else:  
        return render(request, 'firmenadmin_zugriff_verweigert.html')

def projekteÜbersichtView(request):
# Wenn Firmenadmin: Zeige Projektübersicht
    if request.user.ist_firmenadmin:
        # Erstelle Dict mit Projekten und Einträgen in Projekt_Mitarbeiter_Mail
        firma = request.user.firma
        liste_pj_fa_mail = Projekt_Firma_Mail.objects.filter(firma = firma)
        dict_projekte = {}
        for eintrag in liste_pj_fa_mail:
            projekt_bezeichnung = eintrag.projekt.bezeichnung
            projekt_id = eintrag.projekt.id
            pj_fa_mail = Projekt_Firma_Mail.objects.get(projekt = eintrag.projekt, firma = firma)
            liste_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.filter(projekt = eintrag.projekt, mitarbeiter__firma = firma)

            dict_einzelprojekt = {}
            dict_einzelprojekt['liste_pj_ma_mail'] = liste_pj_ma_mail
            dict_einzelprojekt['pj_fa_mail'] = pj_fa_mail
            dict_einzelprojekt['projekt_id'] = projekt_id
            dict_projekte[projekt_bezeichnung] = dict_einzelprojekt

        # Mitarbeiterliste für Dropdown für Mitarbeiter zuweisen
        liste_mitarbeiter = firma.mitarbeiter_set.all()

        context = {
            'dict_projekte':dict_projekte,
            'liste_mitarbeiter':liste_mitarbeiter
        }
        return render(request, 'projekte_übersicht.html', context)

    # Wenn nicht Firmenadmin: Zugriff verweigert
    else:  
        return render(request, 'firmenadmin_zugriff_verweigert.html')

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
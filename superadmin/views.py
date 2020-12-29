from django.shortcuts import render
from .forms import FirmaNeuForm, FirmenAdminNeuForm, ProjektNeuForm
from .models import Firma, Projekt, Projekt_Firma_Mail, Projekt_Mitarbeiter_Mail
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, HttpResponse

def firmaNeuView(request):
    # Wenn Post-Request, dann neue Firma mitsamt Firmenadmin anlegen
    if request.method == 'POST':
        # Bound Form für Neue Firma mit den ausgefüllten Daten erstellen
        firma_neu_daten = FirmaNeuForm(request.POST)
        if firma_neu_daten.is_valid():
            neue_firma = firma_neu_daten.save()
        # Bound Form für Neuen Firmenadmin mit den ausgefüllten Daten (also 'password') erstellen
        firmenadmin_neu_daten = FirmenAdminNeuForm(request.POST)
        if firmenadmin_neu_daten.is_valid():
            User = get_user_model()
            neuer_firmenadmin = User.objects.create_user(
                firma = neue_firma,
                ist_firmenadmin = True,
                username = neue_firma.kurzbezeichnung,
                first_name = neue_firma.kurzbezeichnung,
                last_name = 'Admin',
                email = neue_firma.kurzbezeichnung + '@gernotbau.at',
                password = firmenadmin_neu_daten.cleaned_data['password1'],
            )
            # Weiterleitung zur Neue-Firma-Erfolgsseite
            return render(request, 'firma_neu_bestätigung.html')
    else:
        firma_neu_form = FirmaNeuForm()
        firmenadmin_neu_form = FirmenAdminNeuForm()
        context = {
            'firma_neu_form':firma_neu_form,
            'firmenadmin_neu_form':firmenadmin_neu_form
        }
        # Weiterleitung zur Formularseite für Neue Firma
        return render(request, 'firma_neu_formular.html', context)

def projektNeuView(request):
    # Wenn Post-Request, dann neues Projekt anlegen
    if request.method == 'POST':
        projekt_neu_daten = ProjektNeuForm(request.POST)
        if projekt_neu_daten.is_valid():
            # Neues Projekt aus den Formulardaten anlegen:
            neues_projekt = Projekt.objects.create(
                bezeichnung = projekt_neu_daten.cleaned_data['bezeichnung'],
                kurzbezeichnung = projekt_neu_daten.cleaned_data['kurzbezeichnung']
            )
            # Eintrag in Through-Tabelle Projekt_Firma_Email
            neues_projekt_mail = Projekt_Firma_Mail.objects.create(
                ist_projektadmin = True,
                email = neues_projekt.kurzbezeichnung + "@gernotbau.at",
                projekt = neues_projekt,
                firma = projekt_neu_daten.cleaned_data['firma']
            )
            #Weiterleitung zur Neues-Projekt-Erfolgsseite
            return render(request, 'projekt_neu_bestätigung.html')
    else:
        projekt_neu_form = ProjektNeuForm()
        # Weiterleitung zur Formularseite für Neues Projekt
        return render(request, 'projekt_neu_formular.html', {'projekt_neu_form':projekt_neu_form})

def homeView(request):
    
    if request.user.is_authenticated:
        # Projekte holen, für die der User Projektadmin ist
        liste_pj_ma_mail = Projekt_Mitarbeiter_Mail.objects.filter(mitarbeiter = request.user)
        context = {'liste_pj_ma_mail':liste_pj_ma_mail}
        # Projekte holen, denen der User zugeordnet sind


    return render(request, 'home.html', context)
    #return HttpResponse('HOME')
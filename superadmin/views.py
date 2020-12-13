from django.shortcuts import render
from .forms import FirmaNeuForm, FirmenAdminNeuForm
from .models import Firma
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect

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
        # Weiterleitung zur Neue-Firma-Erfolgsseite
        return render(request, 'firma_neu_formular.html', context)
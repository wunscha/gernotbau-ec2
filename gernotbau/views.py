from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.urls import reverse
from funktionen import hole_dicts

def home_view(request):
    
    # Prüfung Login
    if not request.user.is_authenticated:
        return render(request, './registration/login.html')
    else:
        # Wenn Firmenadmin Weiterleitung zu Firmenadmin-Bereich
        if request.user.ist_firmenadmin:
            return HttpResponseRedirect(reverse('firmenadmin:übersicht_mitarbeiter'))

        else:
            # Projekte holen, für die der User Projektadmin ist
            liste_projekte_user_projektadmin = hole_dicts.projekte_user_projektadmin(request.user)
            
            # Projekte holen, denen der User zugeordnet sind
            liste_projekte_user = hole_dicts.projekte_user(request.user)
            
            context={
                'liste_projekte_user_projektadmin': liste_projekte_user_projektadmin,
                'liste_projekte_user': liste_projekte_user
            }

            return render(request, 'home.html', context)

def login_view(request):

    # Wenn POST: User authentifizieren und einloggen und Weiterleitung zu Home
    if request.method == 'POST':
        # User authentifizieren
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password) # Gibt User-Objekt zurück, wenn Daten vorhanden
        
        # Wenn user in DB vorhanden: Log in
        if user is not None:
            login(request, user)
        
            # Weiterleitung zu Home:
            return HttpResponseRedirect(reverse('kommunikation:übersicht_eingang'))
            # return HttpResponseRedirect(reverse('home'))

        # Wenn user nicht vorhanden: Formular neu laden
        else:
            # Anzeige Fehlermeldung, wenn Login fehlgeschlagen
            context = {'fehlermeldung': 'Sie konnten nicht eingeloggt werden'}
            return render(request, './registration/login.html', context)

    # Wenn GET etc.: Zeige Login-Formular
    else:
        return render(request, './registration/login.html')
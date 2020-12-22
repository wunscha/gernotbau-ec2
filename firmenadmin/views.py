from django.shortcuts import render
from django.contrib.auth import get_user_model
from superadmin.models import Projekt_Mitarbeiter_Mail
from django.http import HttpResponse


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
    return HttpResponse("Mitarbeiter Neu")

def projekteÜbersichtView(request):
    return HttpResponse("Projekte Übersicht")

def workflowsÜbersichtView(request):
    return HttpResponse("Workflows Übersicht")
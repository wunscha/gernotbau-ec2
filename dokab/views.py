from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from projektadmin.funktionen import Ordnerbaum
from projektadmin.models import Ordner_Firma_Freigabe, Ordner
from superadmin.models import Firma, Projekt
from .funktionen import user_hat_ordnerzugriff

#############################################################
# Ordner

def weiterleitung_root(request, projekt_id):
# Leite weiter zur Anzeige Root-Ordner
    projekt = Projekt.objects.get(pk = projekt_id)
    root_ordner = Ordner.objects.get(projekt = projekt, ist_root_ordner = True)

    return HttpResponseRedirect(reverse('dokab:ordner_inhalt', args = [projekt_id, root_ordner.id]))

def ordner_inhalt(request, projekt_id, ordner_id):
# Zeige Ordnerinhalt, wenn User eingeloggt und Ordnerzugriff
    
    if request.user.is_authenticated:
        # Erstelle dict für Anzeige Ordnerbaum:
        # Hole Ordnerstruktur
        projekt = Projekt.objects.get(pk = projekt_id)
        liste_ordner = Ordner.objects.filter(projekt = projekt)
        ordner_root = Ordner.objects.get(projekt = projekt, ist_root_ordner = True)
        # Erstelle Instanz von Ordnerbaum und befülle dict_ordnerbaum für context
        ordnerbaum_instanz = Ordnerbaum()
        dict_ordnerbaum = ordnerbaum_instanz.erstelle_dict_ordnerbaum(liste_ordner, ordner_root)
        # Hole Ordnerfreigaben für die Firma
        firma = request.user.firma
        ordnerbaum = []
        for key, value in dict_ordnerbaum.items():
            # Hole Eintrag in Ordner_Firma_Freigabe, wenn vorhanden, sonst erstelle Neuen Eintrag
            '''
            # TODO: 
            # Vorteil --> Es muüssen nicht alle Freigabe-Einträge neu erstellt wenn neuer Ordner od. Firma angelegt wird; 
            # Nachteil --> Evtl. Erzeugung von doppelten Einträgen möglich, oder Freigabe werden überschrieben?
            '''
            ordner_firma_freigabe = Ordner_Firma_Freigabe.objects.get_or_create(
                firma = firma, 
                ordner = value, 
                defaults = {
                    'projekt':projekt, 
                    'freigabe_lesen':False, 
                    'freigabe_upload':False
                    }
                )
            
            # Dict Einzelordner befüllen
            dict_einzelordner = {}
            dict_einzelordner['ordner_darstellung'] = key
            dict_einzelordner['ordner'] = value
            dict_einzelordner['ordner_freigabe_lesen'] = ordner_firma_freigabe[0].freigabe_lesen # Index erforderlich wegen 'get_or_create'
            dict_einzelordner['ordner_freigabe_upload'] = ordner_firma_freigabe[0].freigabe_upload # Index erforderlich wegen 'get_or_create'

            # Ordnerbaum befüllen
            ordnerbaum.append(dict_einzelordner)

        # Packe Context und renedere Ordnerinhalt
        context = {
            'projekt_id':projekt_id,
            'ordner_id':ordner_id,
            'ordnerbaum':ordnerbaum
        }

        if user_hat_ordnerzugriff(user = request.user, ordner_id = ordner_id, projekt_id = projekt_id):
            return render(request, 'ordner_inhalt.html', context)
        
        else:
            return render(request, 'dokab_ordner_zugriff_verweigert.html', context)

#############################################################
# Workflows

def workflows_übersicht(request, projekt_id):
# Zeige Workflows des Users für das Projekt
    return HttpResponse('Workflows Übersicht')
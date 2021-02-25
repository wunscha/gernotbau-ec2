from django.core import exceptions
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from gernotbau.settings import DB_SUPER
from projektadmin.models import Mitarbeiter

class Nachricht(models.Model):
    verfasser = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    text = models.CharField(max_length = 300)
    betreff = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

    def _liste_empfänger(self):
        li_empf = []
        for nr_empf in Nachricht_Empfänger.objects.using(DB_SUPER).filter(nachricht = self):
            li_empf.append(nr_empf.empfänger)
        
        return li_empf

    def _liste_empfänger_dict(self):
        li_empf_dict = []
        for nr_empf in Nachricht_Empfänger.objects.using(DB_SUPER).filter(nachricht = self):
            empf_dict = nr_empf.empfänger.__dict__
            empf_dict['gelesen'] = nr_empf._gelesen()
            li_empf_dict.append(empf_dict)

        return li_empf_dict

class Nachricht_Empfänger(models.Model):
    nachricht = models.ForeignKey(Nachricht, on_delete = models.CASCADE)
    empfänger = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    # Zeitstempel nicht notwendig
    
    def _gelesen(self):
        qs_gelesen = Nachricht_Empfänger_Gelesen.objects.using(DB_SUPER).filter(nachricht_empfänger = self)
        if qs_gelesen:
            return True
        else:
            return False

class Nachricht_Empfänger_Gelesen(models.Model):
    nachricht_empfänger = models.ForeignKey(Nachricht_Empfänger, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()


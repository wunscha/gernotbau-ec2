from django.db import models
from superadmin.models import Mitarbeiter
from projektadmin.models import Ordner

class Paket(models.Model):
    bezeichnung = models.CharField(max_length = 30)

    def __str__(self):
        return self.bezeichnung

class Dokument(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    pfad = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.PROTECT)
    paket = models.ForeignKey(Paket, on_delete = models.PROTECT)
    ordner = models.ForeignKey(Ordner, on_delete = models.PROTECT)

    def __str__(self):
        return self.bezeichnung
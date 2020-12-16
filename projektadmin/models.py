from django.db import models
from superadmin.models import Projekt, Firma

#########################################
# Workflows

class Workflow_Schema(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)

    def __str__(self):
        return self.bezeichnung

class Workflow_Schema_Stufe(models.Model):
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    vorstufe = models.ForeignKey('self', on_delete = models.PROTECT, null=True, blank=True)
    prüffirma = models.ManyToManyField(Firma)
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)
    # Feld 'mitarbeiter' wird bei der Implementierung der app firmenadmin eingefügt

    def __str__(self):
        return str('WFSch-Stufe_für_' + self.workflow_schema.bezeichnung)

#########################################
# Ordner

class Ordner(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    ist_root_ordner = models.BooleanField(default = False)
    überordner = models.ForeignKey('self', on_delete = models.CASCADE, null = True, blank = True)
    firma = models.ManyToManyField(Firma, through = 'Ordner_Firma_Freigabe')
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)

    def __str__(self):
        return self.bezeichnung

class Ordner_Firma_Freigabe(models.Model):
    freigabe_lesen = models.BooleanField()
    freigabe_upload = models.BooleanField()
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)

    def __str__(self):
        return str('%s - %s' % (self.ordner.bezeichnung, self.firma.kurzbezeichnung,))

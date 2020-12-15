from django.db import models
from superadmin.models import Projekt, Firma

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
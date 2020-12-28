from django.db import models
from superadmin.models import Projekt, Firma, Mitarbeiter

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
    mitarbeiter = models.ManyToManyField(Mitarbeiter, through='WFSch_Stufe_Mitarbeiter')
    
    def __str__(self):
        return str('WFSch-Stufe_für_' + self.workflow_schema.bezeichnung)

class WFSch_Stufe_Mitarbeiter(models.Model):
    immer_erforderlich = models.BooleanField()
    wfsch_stufe = models.ForeignKey(Workflow_Schema_Stufe, on_delete = models.CASCADE)
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE)

    def __str__(self):
        return str('%s - %s' % (self.wfsch_stufe.workflow_schema.bezeichnung, self.mitarbeiter.last_name,))

#########################################
# Ordner

class Ordner(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    ist_root_ordner = models.BooleanField(default = False)
    überordner = models.ForeignKey('self', on_delete = models.CASCADE, null = True, blank = True)
    firma = models.ManyToManyField(Firma, through = 'Ordner_Firma_Freigabe')
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.PROTECT, null = True, blank = True)
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

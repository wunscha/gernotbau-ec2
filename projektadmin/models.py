from django.db import models
from django.utils import timezone
from superadmin.models import Projekt, Firma, Mitarbeiter

#########################################
# Workflows

class Workflow_Schema(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    
    def __str__(self):
        return self.bezeichnung

class Workflow_Schema_Stufe(models.Model):
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    vorstufe = models.ForeignKey('self', on_delete = models.DO_NOTHING, null=True, blank=True)
    bezeichnung = models.CharField(max_length = 20, null = True)
    
    def __str__(self):
        return str('WFSch-Stufe_für_' + self.workflow_schema.bezeichnung)

class WFSch_Stufe_Firma(models.Model):
    workflow_schema_stufe = models.ForeignKey(Workflow_Schema_Stufe, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length=20)

    def __str__(self):
        return str('Prüffirma für ' + self.workflow_schema_stufe.workflow_schema.bezeichnung)

class WFSch_Stufe_Mitarbeiter(models.Model):
    immer_erforderlich = models.BooleanField()
    wfsch_stufe = models.ForeignKey(Workflow_Schema_Stufe, on_delete = models.CASCADE)
    mitarbeiter_id = models.CharField(max_length=20, default='Das ist nicht gültig')
    gelöscht = models.BooleanField(default = False)
    zeitstempel = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return str('%s - %s' % (self.wfsch_stufe.workflow_schema.bezeichnung, self.mitarbeiter.last_name,))

#########################################
# Ordner

class Ordner(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    ist_root_ordner = models.BooleanField(default = False)
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.PROTECT, null = True, blank = True)
    unterordner = models.ManyToManyField('self', through='Überordner_Unterordner')
    # TODO: Beim neuen Aufsetzen von DB: M2M-Feld 'unterordner' mit through = 'Überordner_Unterordner' einfügen
    
    def __str__(self):
        return self.bezeichnung

class Überordner_Unterordner(models.Model):
    überordner = models.ForeignKey(Ordner, on_delete = models.CASCADE, related_name = 'rel_überordner') # related_name notwendig, weil es sonst zu 'reverse accessor clash' kommt
    unterordner = models.ForeignKey(Ordner, on_delete = models.CASCADE, related_name = 'rel_unterordner') # related_name notwendig, weil es sonst zu 'reverse accessor clash' kommt

    def __str__(self):
        return self.überordner.bezeichnung + '-' + self.unterordner.bezeichnung

class Ordner_Firma_Freigabe(models.Model):
    freigabe_lesen = models.BooleanField()
    freigabe_upload = models.BooleanField()
    freigaben_erben = models.BooleanField(default = True)
    firma_id = models.CharField(max_length = 20, null = True) # TODO: 'nullable' entfernen --> war nur für Testphase nötig
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)

    def __str__(self):

        lesen = ''
        if self.freigabe_lesen:
            lesen = 'Lesen '
            
        upload = ''
        if self.freigabe_upload:
            upload = 'Upload'

        return str('%s - %s %s%s' % (self.ordner.bezeichnung, self.firma_id, lesen, upload))

'''
class Update_Ordner_Worfkflow_Schema(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Update_Ordner_Freigabe_Lesen(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length = 20)
    freigabe_lesen = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Update_Ordner_Freigabe_Upload(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length = 20)
    freigabe_upload = models.BooleanField()
    zeitstempel = models.DateTimeField
'''

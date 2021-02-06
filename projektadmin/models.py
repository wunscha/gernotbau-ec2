from django import db
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

    #######################################
    # Neue Herangehensweise (Funktionen in Models definieren) 06.02.2021

    def verbindung_rolle_herstellen(self, db_bezeichnung, rolle):
        verbindung_ordner_rolle = Ordner_Rolle.objects.using(db_bezeichnung).get_or_create(
            ordner = self,
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )
        verbindung_ordner_rolle.aktualisieren(db_bezeichnung)

    # LESEFREIGABE ROLLE
    def lesefreigabe_erteilen_rolle(self, db_bezeichnung, rolle):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )
    
    def lesefreigabe_entziehen_rolle(self, db_bezeichnung, rolle):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_rolle(self, db_bezeichnung, rolle):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        return Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).filter(Ordner_Firma = o_fa).latest('zeitstempel').freigabe_lesen

    # UPLOADFREIGABE ROLLE
    def uploadfreigabe_erteilen_rolle(self, db_bezeichnung, rolle):
        pass

    def uploadfreigabe_entziehen_rolle(self, db_bezeichnung, rolle):
        pass

    def uploadreigabe_rolle(self, db_bezeichnung, rolle):
        pass

    # LESEFREIGABE FIRMA
    def lesefreigabe_erteilen_firma(self, db_bezeichnung, firma):
        pass

    def lesefreigabe_entziehen_firma(self, db_bezeichnung, firma):
        pass

    def lesefreigabe_firma(self, db_bezeichnung, firma):
        pass

    # UPLOADFREIGABE FIRMA
    def uploadfreigabe_erteilen_firma(self, db_bezeichnung, firma):
        pass

    def uploadfreigabe_entziehen_firma(self, db_bezeichnung, firma):
        pass

    def uploadfreigabe_firma(self, db_bezeichnung, firma):
        pass

    

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

##################################
# Models Projektstruktur

class Rolle(models.Model):
    zeitstempel = models.DateTimeField()

    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        Rolle_Bezeichnung.objects.using(db_bezeichnung).create(
            rolle = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return Rolle_Bezeichnung.objects.using(db_bezeichnung).filter(rolle = self).latest('zeitstempel').bezeichnung

    def löschen(self, db_bezeichnung):
        Rolle_Gelöscht.objects.using(db_bezeichnung).create(
            rolle = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return Rolle_Gelöscht.objects.using(db_bezeichnung).fiter(rolle = self).latest('zeitstempel').gelöscht

class Rolle_Gelöscht(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Rolle_Bezeichnung(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField

class Rolle_Firma(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

class Rolle_Firma_Aktiv(models.Model):
    rolle_firma = models.ForeignKey(Rolle_Firma, on_delete = models.CASCADE)
    aktiv = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ordner_Rolle(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        Ordner_Rolle_Aktuell.objects.using(db_bezeichnung).create(
            ordner_rolle = self,
            aktuell = True, 
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return Ordner_Rolle_Aktuell.objects.using(db_bezeichnung).filter(ordner_rolle = self).latest('zeitstempel').aktuell

class Ordner_Rolle_Aktuell(models.Model):
    ordner_rolle = models.ForeignKey(Ordner_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Freigabe_Lesen_Rolle(models.Model):
    ordner_rolle = models.ForeignKey(Ordner_Rolle, on_delete = models.CASCADE)
    freigabe_lesen = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Freigabe_Upload_Rolle(models.Model):
    ordner_rolle = models.ForeignKey(Ordner_Rolle, on_delete = models.CASCADE)
    freigabe_upload = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ordner_Firma(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE, null = True) #TODO: Nullable entfernen
    firma_id = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField

class Freigabe_Lesen_Firma(models.Model):
    ordner_rolle_firma = models.ForeignKey(Ordner_Firma, on_delete = models.CASCADE)
    freigabe_lesen = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Freigabe_Upload_Firma(models.Model):
    ordner_rolle_firma = models.ForeignKey(Ordner_Firma, on_delete = models.CASCADE)
    freigabe_upload = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ordner_WFSch(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    wfsch = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            ordner_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            ordner_wfsch = self,
            aktuelle = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).filter(ordner_wfsch = self).latest('zeitstempel').aktuell

class Ordner_WFSch_Aktuell(models.Model):
    ordner_wfsch = models.ForeignKey(Ordner_WFSch, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Rolle(models.Model):
    wfsch_stufe = models.ForeignKey(Workflow_Schema_Stufe, on_delete = models.CASCADE)
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        WFSch_Stufe_Rolle_Aktuell.objects.using(db_bezeichnung).create(
            wfsch_stufe_rolle = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self, db_bezeichnung):
        WFSch_Stufe_Rolle_Aktuell.objects.using(db_bezeichnung).create(
            wfsch_stufe_rolle = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return WFSch_Stufe_Rolle_Aktuell.objects.using(db_bezeichnung).filter(wfsch_stufe_rolle = self).latest('zeitstempel').aktuell

class WFSch_Stufe_Rolle_Aktuell(models.Model):
    wfsch_stufe_rolle = models.ForeignKey(WFSch_Stufe_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Projektstruktur(models.Model):
    zeitstempel = models.DateTimeField()
    projektstruktur_id = models.CharField(max_length = 20)
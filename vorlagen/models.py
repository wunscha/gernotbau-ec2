from datetime import time
from django import db
from django.db import models
from django.db.models.fields import DateTimeField
from django.db.models.fields.related import OneToOneField
from django.utils import timezone

# Create your models here.

class V_Ordner(models.Model):
    zeitstempel = models.DateTimeField()
    ist_root_ordner = models.BooleanField()

    def bezeichnung(self, db_bezeichnung):
        return V_Ordner_Bezeichnung.objects.using(db_bezeichnung).filter(v_ordner = self).latest('zeitstempel').bezeichnung

    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_Ordner_Bezeichnung.objects.using(db_bezeichnung).create(
            v_ordner = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def freigabe_lesen(self, db_bezeichnung, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(db_bezeichnung).get(v_ordner = self, v_rolle = v_rolle)
        return V_Ordner_Freigabe_Lesen.objects.using(db_bezeichnung).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_lesen

    def lesefreigabe_erteilen(self, db_bezeichnung, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(db_bezeichnung).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Lesen.objects.using(db_bezeichnung).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_entziehen(self, db_bezeichnung, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(db_bezeichnung).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Lesen.objects.using(db_bezeichnung).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_erteilen(self, db_bezeichnung, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(db_bezeichnung).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Upload.objects.using(db_bezeichnung).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_upload = True,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen(self, db_bezeichnung, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(db_bezeichnung).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Upload.objects.using(db_bezeichnung).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    def liste_unterordner(self, db_bezeichnung):
    # Gibt Liste der aktuellen Unterordner zurück
        qs_v_ordner_unterordner = V_Ordner_Unterordner.objects.using(db_bezeichnung).filter(v_überordner = self)
        li_unterordner = []
        for e in qs_v_ordner_unterordner:
            if e.aktuell(db_bezeichnung) and not e.gelöscht(db_bezeichnung): li_unterordner.append(e.v_unterordner)
        return li_unterordner

    def löschen(self, db_bezeichnung):
        V_Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            v_ordner = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )

            # TODO: Prüfen ob Dokumente, Unterordner etc. verknüpft

    def gelöscht(self, db_bezeichnung):
        return V_Ordner_Gelöscht.objects.using(db_bezeichnung).filter(v_ordner = self).latest('zeitstempel').gelöscht

class V_Ordner_Gelöscht(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Unterordner(models.Model):
    v_überordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_überordner')
    v_unterordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_unterordner')
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_Ordner_Unterordner_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_unterordner = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualiseren(self, db_bezeichnung):
        V_Ordner_Unterordner_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_unterordner = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_Ordner_Unterordner_Aktuell.objects.using(db_bezeichnung).filter(v_ordner_unterordner = self).latest('zeitstempel').aktuell

class V_Ordner_Unterordner_Aktuell(models.Model):
    v_ordner_unterordner = models.ForeignKey(V_Ordner_Unterordner, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Bezeichnung(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class V_Rolle(models.Model):
    zeitstempel = models.DateTimeField()

    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_Rolle_Bezeichnung.objects.using(db_bezeichnung).create(
            v_rolle = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_Rolle_Bezeichnung.objects.using(db_bezeichnung).filter(v_rolle = self).latest('zeitstempel').bezeichnung

    def löschen(self, db_bezeichnung):
        V_Rolle_Gelöscht.objects.using(db_bezeichnung).create(
            v_rolle = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_Rolle_Gelöscht.objects.using(db_bezeichnung).fiter(v_rolle = self).latest('zeitstempel').gelöscht

class V_Rolle_Gelöscht(models.Model):
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Rolle_Bezeichnung(models.Model):
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField

class V_Ordner_Rolle(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_Ordner_Rolle_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_rolle = self,
            aktuell = True, 
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_Ordner_Rolle_Aktuell.objects.using(db_bezeichnung).filter(v_ordner_rolle = self).latest('zeitstempel').aktuell

class V_Ordner_Rolle_Aktuell(models.Model):
    v_ordner_rolle = models.ForeignKey(V_Ordner_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Freigabe_Lesen(models.Model):
    v_ordner_rolle = models.ForeignKey(V_Ordner_Rolle, on_delete = models.CASCADE)
    freigabe_lesen = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Freigabe_Upload(models.Model):
    v_ordner_rolle = models.ForeignKey(V_Ordner_Rolle, on_delete = models.CASCADE)
    freigabe_upload = models.BooleanField()
    zeitstempel = models.DateTimeField()


class V_Workflow_Schema(models.Model):
    zeitstempel = models.DateTimeField()

    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_WFSch_Bezeichnung.objects.using(db_bezeichnung).create(
            v_wfsch = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_WFSch_Bezeichnung.objects.using(db_bezeichnung).filter(v_wfsch = self).latest('zeitstempel').bezeichnung

    def löschen(self, db_bezeichnung):
        V_WFSch_Gelöscht.object.using(db_bezeichnung).create(
            v_wfsch = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_WFSch_Gelöscht.objects.using(db_bezeichnung).filter(v_wfsch = self).lateste('zeitstempel').bezeichnung

class V_WFSch_Gelöscht(models.Model):
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Bezeichnung(models.Model):
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe(models.Model):
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_WFSch_Bezeichnung.objects.using(db_bezeichnung).create(
            v_wfsch_stufe = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_WFSch_Bezeichnung.objects.using(db_bezeichnung).filter(v_wfsch_stufe = self).latest('zeitstempel').bezeichnung

    def löschen(self, db_bezeichnung):
        V_WFSch_Gelöscht.objects.using(db_bezeichnung).create(
            v_wfsch_stufe = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).filter(v_wfsch_stufe = self).latest('zeitstempel').gelöscht

class V_WFSch_Stufe_Gelöscht(models.Model):
    v_wfsch_stufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe_Folgestufe(models.Model):
    v_wfsch_stufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE, related_name = 'v_wfsch_stufe')
    v_wfsch_folgestufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE, related_name = 'v_wfsch_folgestufe')
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_WFSch_Stufe_Folgestufe.objects.using(db_bezeichnung).create(
            v_wfsch_stufe_folgestufe = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        V_WFSch_Stufe_Folgestufe.objects.using(db_bezeichnung).create(
            v_wfsch_stufe_folgestufe = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_WFSch_Stufe_Folgestufe_Aktuell.objects.using(db_bezeichnung).filter(v_wfsch_stufe_folgestufe = self).aktuell

class V_WFSch_Stufe_Folgestufe_Aktuell(models.Model):
    v_wfsch_stufe_folgestufe = models.ForeignKey(V_WFSch_Stufe_Folgestufe, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe_Bezeichnung(models.Model):
    v_wfsch_stufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()

class V_Ordner_WFSch(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        V_Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_wfsch = self,
            aktuelle = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).filter(v_ordner_wfsch = self).latest('zeitstempel').aktuell

class V_Ordner_WFSch_Aktuell(models.Model):
    v_ordner_wfsch = models.ForeignKey(V_Ordner_WFSch, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe_Rolle(models.Model):
    v_wfsch_stufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE)
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_WFSch_Stufe_Rolle_Aktuell.objects.using(db_bezeichnung).create(
            v_wfsch_stufe_rolle = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self, db_bezeichnung):
        V_WFSch_Stufe_Rolle_Aktuell.objects.using(db_bezeichnung).create(
            v_wfsch_stufe_rolle = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_WFSch_Stufe_Rolle_Aktuell.objects.using(db_bezeichnung).filter(v_wfsch_stufe_rolle = self).latest('zeitstempel').aktuell

class V_WFSch_Stufe_Rolle_Aktuell(models.Model):
    v_wfsch_stufe_rolle = models.ForeignKey(V_WFSch_Stufe_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Projektstruktur(models.Model):
    zeitstempel = models.DateTimeField()

    def ordner_hinzufügen(self, db_bezeichnung, v_ordner):
        # Verbindung anlegen, wenn noch nicht vorhanden
        verbindung_zu_ordner = V_PJS_Ordner.objects.using(db_bezeichnung).get_or_create(
            v_pjs = self,
            v_ordner = v_ordner,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_zu_ordner.aktualisieren(db_bezeichnung)

    def ordner_entfernen(self, db_bezeichnung, v_ordner):
        verbindung_zu_ordner = V_PJS_Ordner.objects.using(db_bezeichnung).get(
            v_pjs = self,
            v_ordner = v_ordner)
        verbindung_zu_ordner.entaktualisieren(db_bezeichnung)

    def wfsch_hinzufügen(self, db_bezeichnung, v_wfsch):
        # Verbindung anlegen, wenn noch nicht vorhanden
        verbindung_zu_wfsch = V_PJS_WFSch.objects.using(db_bezeichnung).get_or_create(
            v_pjs = self,
            v_wfsch = v_wfsch,
            defaults = {'zeitstempel':timezone.now()}
            )[0]
        verbindung_zu_wfsch.aktualisieren(db_bezeichnung)

    def wfsch_entfernen(self, db_bezeichnung, v_wfsch):
        verbindung_zu_wfsch = V_PJS_WFSch.objects.using(db_bezeichnung).get(
            v_pjs = self,
            v_wfsch = v_wfsch
            )
        verbindung_zu_wfsch.entaktualisieren(db_bezeichnung)

class V_PJS_Ordner(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_PJS_Ordner_Aktuell.objects.using(db_bezeichnung).create(
            v_pjs_ordner = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        V_PJS_Ordner_Aktuell.objects.using(db_bezeichnung).create(
            v_pjs_ordner = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_PJS_Ordner_Aktuell.objects.using(db_bezeichnung).filter(v_pjs_ordner = self).lateste('zeitstempel').aktuell

class V_PJS_Ordner_Aktuell(models.Model):
    v_pjs_ordner = models.ForeignKey(V_PJS_Ordner, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_PJS_WFSch(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self, db_bezeichnung):
        V_PJS_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            v_pjs_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        V_PJS_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            v_pjs_wfsch = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_PJS_WFSch_Aktuell.objects.using(db_bezeichnung).filter(v_pjs_wfsch = self).latest('zeitstempel').aktuell

class V_PJS_WFSch_Aktuell(models.Model):
    v_pjs_wfsch = models.ForeignKey(V_PJS_WFSch, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

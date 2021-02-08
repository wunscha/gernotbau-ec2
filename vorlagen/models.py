from datetime import time
from django import db
from django.db import models
from django.db.models.fields import DateTimeField
from django.db.models.fields.related import OneToOneField
from django.utils import timezone


from projektadmin.models import Ordner, Ordner_Vorlage, Ordner_Unterordner, Workflow_Schema
# Create your models here.

class V_Ordner(models.Model):
    zeitstempel = models.DateTimeField()
    ist_root_ordner = models.BooleanField()

    # V_ORDNER BEZEICHNUNG
    def bezeichnung(self, db_bezeichnung):
        return V_Ordner_Bezeichnung.objects.using(db_bezeichnung).filter(v_ordner = self).latest('zeitstempel').bezeichnung

    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_Ordner_Bezeichnung.objects.using(db_bezeichnung).create(
            v_ordner = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    # V_ORDNER FREIGABE LESEN
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

    # V_ORDNER FREIGABE UPLOAD
    def freigabe_upload(self, db_bezeichnung, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(db_bezeichnung).get(v_ordner = self, v_rolle = v_rolle)
        return V_Ordner_Freigabe_Upload.objects.using(db_bezeichnung).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_upload

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

    # V_ORDNER UNTERORDNER
    def unterordner_anlegen(self, db_bezeichnung, *, bezeichnung_unterordner):
        neuer_unterordner = V_Ordner.objects.using(db_bezeichnung).create(
            zeitstempel = timezone.now(),
            ist_root_ordner = False,
            )
        neuer_unterordner.bezeichnung_ändern(db_bezeichnung, bezeichnung_unterordner)
        # Mit "nicht gelöscht" initialisieren
        V_Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            v_ordner = neuer_unterordner,
            gelöscht = False,
            zeitstempel = timezone.now()
            )
        # Verbindung Ordner-Unterordner anlegen
        neue_verbindung_ordner_unterordner = V_Ordner_Unterordner.objects.using(db_bezeichnung).create(
            v_ordner = self,
            v_unterordner = neuer_unterordner,
            zeitstempel = timezone.now()
            )
        neue_verbindung_ordner_unterordner.aktualisieren(db_bezeichnung)

    def liste_unterordner(self, db_bezeichnung):
    # Gibt Liste der aktuellen Unterordner zurück
        qs_v_ordner_unterordner = V_Ordner_Unterordner.objects.using(db_bezeichnung).filter(v_ordner = self)
        li_unterordner = []
        for e in qs_v_ordner_unterordner:
            if e.aktuell(db_bezeichnung) and not e.v_unterordner.gelöscht(db_bezeichnung): li_unterordner.append(e.v_unterordner)
        return li_unterordner

    # V_ORDNER LÖSCHEN
    def löschen(self, db_bezeichnung):
        V_Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            v_ordner = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )
        # Verbindung zu Überordner lösen
        verbindung_zu_überordner = V_Ordner_Unterordner.objects.using(db_bezeichnung).get(unterordner = self)
        verbindung_zu_überordner.entaktualisieren(db_bezeichnung)
        # Verbindungen zu Unterordnern lösen
        # TODO: Gesamter Baum unterhalb Ordner sollte gelöscht werden (Ordner und Verbindungen)
        for uo in self.liste_unterordner(db_bezeichnung):
            verbindung_zu_unterordner = V_Ordner_Unterordner.objects.using(db_bezeichnung).get(unterordner = uo)
            verbindung_zu_unterordner.entaktualisieren(db_bezeichnung)

    def gelöscht(self, db_bezeichnung):
        return V_Ordner_Gelöscht.objects.using(db_bezeichnung).filter(v_ordner = self).latest('zeitstempel').gelöscht

    # V_ORDNER -> ORDNER IN DB ANLEGEN
    def in_db_anlegen(self,* ,db_bezeichnung_quelle, db_bezeichnung_ziel):
        # Ordner anlegen
        neuer_ordner = Ordner.objects.using(db_bezeichnung_ziel).create(
            ist_root_ordner = self.ist_root_ordner,
            zeitstempel = timezone.now()
            )
        neuer_ordner.entlöschen(db_bezeichnung_ziel)
        neuer_ordner.bezeichnung_ändern(db_bezeichnung_ziel, neue_bezeichnung = self.bezeichnung(db_bezeichnung_quelle))
        # Verbindung zu Vorlage
        Ordner_Vorlage.objects.using(db_bezeichnung_ziel).create(
            ordner = neuer_ordner,
            v_ordner_id = self.id,
            )

class V_Ordner_Gelöscht(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Unterordner(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_ordner')
    v_unterordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_unterordner')
    zeitstempel = models.DateTimeField()


    # ORDNER-UNTERORDNER AKTUELL
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

    # ORDNER-UNTERORDNER IN DB ANLEGEN
    def in_db_anlegen(self, db_bezeichnung_ziel):
        Ordner_Unterordner.objects.using(db_bezeichnung_ziel).create(
            ordner = Ordner.objects.using(db_bezeichnung_ziel).get(ordner_vorlage__v_ordner_id = self.v_ordner.id),
            unterordner = Ordner.objects.using(db_bezeichnung_ziel).get(ordner_vorlage__v_ordner_id = self.v_unterordner.id),
            zeitstempel = timezone.now()
            )

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

    # V_WORKFLOW_SCHEMA BEZEICHUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_WFSch_Bezeichnung.objects.using(db_bezeichnung).create(
            v_wfsch = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_WFSch_Bezeichnung.objects.using(db_bezeichnung).filter(v_wfsch = self).latest('zeitstempel').bezeichnung

    # V_WORKFLOW_SCHEMA GELÖSCHT
    def löschen(self, db_bezeichnung):
        V_WFSch_Gelöscht.object.using(db_bezeichnung).create(
            v_wfsch = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_WFSch_Gelöscht.objects.using(db_bezeichnung).filter(v_wfsch = self).latest('zeitstempel').bezeichnung

    # V_WORKFLOW_SCHEMA IN DB ANLEGEN
    def in_db_anlegen(self, db_bezeichnung_ziel):
        neues_wfsch = Workflow_Schema.objects.using(db_bezeichnung_ziel).create(
            zeitstempel = timezone.now(),
        )
        # WFSCH in DB anlegen
        # für jede Stufe in liste_stufen:
        #    Stufe anlegen (inkl. Verbindung Stufe_Vorlage)
        #    Verbindung Stufe-Folgestufe anlegen

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

    # PJS BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, bezeichnung):
        V_Projektstruktur_Bezeichnung.objects.using(db_bezeichnung).create(
            v_projektstruktur = self,
            bezeichnung = bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_Projektstruktur_Bezeichnung.objects.using(db_bezeichnung).filter(v_projektstruktur = self).latest('zeitstempel').bezeichnung

    # PJS ORDNER
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

    def liste_ordner(self, db_bezeichnung):
        li_ordner= []
        for v in V_PJS_Ordner.objects.using(db_bezeichnung).filter(v_pjs = self):
            if v.aktuell(db_bezeichnung) and not v.v_ordner.gelöscht(db_bezeichnung):
                li_ordner.append(v.v_ordner)
        return li_ordner

    def root_v_ordner(self, db_bezeichnung):
        for v_pjs_o in V_PJS_Ordner.objects.using(db_bezeichnung).filter(v_pjs = self):
            if v_pjs_o.aktuell(db_bezeichnung):
                v_o = v_pjs_o.v_ordner
                if v_o.ist_root_ordner and not v_o.gelöscht(db_bezeichnung):
                    return v_o

    def ordnerstruktur_in_db_anlegen(self,*, db_bezeichnung_quelle,  db_bezeichnung_ziel):
        # Ordner anlegen (zuerst müssen alle Ordner angelegt werden damit Verbindungen hergestellt werden können)
        for v_o in self.liste_ordner(db_bezeichnung_quelle):
            v_o.in_db_anlegen(db_bezeichnung_quelle = db_bezeichnung_quelle, db_bezeichnung_ziel = db_bezeichnung_ziel)
        
        # Verbindungen Ordner-Unterordner anlegen
        for o in self.liste_ordner(db_bezeichnung_quelle):
            for v in V_Ordner_Unterordner.objects.using(db_bezeichnung_quelle).filter(v_ordner = o):
                if v.aktuell(db_bezeichnung_quelle):
                    v.in_db_anlegen(db_bezeichnung_ziel)

    # PJS WFSCH
    def wfsch_hinzufügen(self, db_bezeichnung, v_wfsch):
        # Verbindung anlegen, wenn noch nicht vorhanden
        verbindung_zu_wfsch = V_PJS_WFSch.objects.using(db_bezeichnung).get_or_create(
            v_pjs = self,
            v_wfsch = v_wfsch,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_zu_wfsch.aktualisieren(db_bezeichnung)

    def wfsch_entfernen(self, db_bezeichnung, v_wfsch):
        verbindung_zu_wfsch = V_PJS_WFSch.objects.using(db_bezeichnung).get(
            v_pjs = self,
            v_wfsch = v_wfsch
            )
        verbindung_zu_wfsch.entaktualisieren(db_bezeichnung)

    # PJS ROLLEN
    def rolle_hinzufügen(self, db_bezeichnung, v_rolle):
        verbindung_zu_rolle = V_PJS_Rolle.objects.using(db_bezeichnung).get_or_create(
            v_pjs = self,
            v_rolle = v_rolle, 
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_zu_rolle.aktivieren(db_bezeichnung)

    def rolle_entfernen(self, db_bezeichnung, v_rolle):
        verbindung_zu_rolle = V_PJS_Rolle.objects.using(db_bezeichnung).get(
            v_pjs = self,
            v_rolle = v_rolle,
            )
        verbindung_zu_rolle.entaktualisieren(db_bezeichnung)

class V_Projektstruktur_Bezeichnung(models.Model):
    projektstruktur = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

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
        return V_PJS_Ordner_Aktuell.objects.using(db_bezeichnung).filter(v_pjs_ordner = self).latest('zeitstempel').aktuell

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

class V_PJS_Rolle(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    v_zeitstempel = models.DateTimeField()

    def aktivieren(self, db_bezeichnung):
        V_PJS_Rolle_Aktiv.objects.using(db_bezeichnung).create(
            v_pjs_rolle = self,
            aktiv = True,
            zeitstempel = timezone.now()
            )

    def entaktivieren(self, db_bezeichnung):
        V_PJS_Rolle_Aktiv.objects.using(db_bezeichnung).create(
            v_pjs_rolle = self,
            aktiv = False,
            zeitstempel = timezone.now()
            )

    def aktiv(self, db_bezeichnung):
        return V_PJS_Rolle_Aktiv.objects.using(db_bezeichnung).filter(v_pjs_rolle = self).latest('zeitstempel').aktiv

class V_PJS_Rolle_Aktiv(models.Model):
    v_pjs_rolle = models.ForeignKey(V_PJS_Rolle, on_delete = models.CASCADE)
    aktiv = models.BooleanField()
    zeitstempel = models.DateTimeField()
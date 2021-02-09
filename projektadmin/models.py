from datetime import time
from django import db
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from superadmin.models import Firma

######################################
# VORLAGEN
#
#

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

    # V_ORDNER_ROLLEN
    def liste_rollen(self, db_bezeichnung):
        li_v_rollen = []
        for verbindung_o_r in V_Ordner_Rolle.objects.filter(v_ordner = self):
            if verbindung_o_r.aktuell(db_bezeichnung) and not verbindung_o_r.v_rolle.gelöscht(db_bezeichnung):
                li_v_rollen.append(verbindung_o_r.v_rolle)
        return li_v_rollen

    # V_ORDNER -> ORDNER IN DB ANLEGEN
    def in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
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
        # Freigaben übernehmen
        neuer_ordner.freigaben_von_vorlage_übernehmen(db_bezeichnung_quelle, db_bezeichnung_ziel)
        
    # V_ORDNER -> ORDNERBAUM
    def ordnerbaum_in_db_anlegen(self, *, db_bezeichnung_quelle, db_bezeichnung_ziel):
        def rekursion_ordnerbaum_anlegen(v_ordner):
        # Legt Ordnerbaum unterhalb von v_ordner in Ziel-DB an
            for v_uo in v_ordner.liste_unterordner(db_bezeichnung_quelle):
                # Ordner anlegen
                v_uo.in_db_anlegen(db_bezeichnung_quelle = db_bezeichnung_quelle, db_bezeichnung_ziel = db_bezeichnung_ziel)
                # Verbindung anlegen
                verbindung_o_uo = Ordner_Unterordner.objects.using(db_bezeichnung_ziel).create(
                    ordner = Ordner.objects.using(db_bezeichnung_ziel).get(ordner_vorlage__v_ordner_id = v_ordner.id),
                    unterordner = Ordner.objects.using(db_bezeichnung_ziel).get(ordner_vorlage__v_ordner_id = v_uo.id),
                    zeitstempel = timezone.now()
                    )
                verbindung_o_uo.aktualisieren(db_bezeichnung_ziel)
                rekursion_ordnerbaum_anlegen(v_uo)
        
        # Zuerst Ordner in DB anlegen, dann unterliegenden Ordnerbaum durch Rekursion anlegen
        self.in_db_anlegen(db_bezeichnung_quelle = db_bezeichnung_quelle, db_bezeichnung_ziel = db_bezeichnung_ziel)
        rekursion_ordnerbaum_anlegen(self)

class V_Ordner_Gelöscht(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Unterordner(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_ordner')
    v_unterordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_unterordner')
    zeitstempel = models.DateTimeField()


    # V_ORDNER-UNTERORDNER AKTUELL
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

    # V_ORDNER-UNTERORDNER IN DB ANLEGEN
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
    
    # V_ROLLE BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_Rolle_Bezeichnung.objects.using(db_bezeichnung).create(
            v_rolle = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_Rolle_Bezeichnung.objects.using(db_bezeichnung).filter(v_rolle = self).latest('zeitstempel').bezeichnung

    # V_ROLLE LÖSCHEN
    def löschen(self, db_bezeichnung):
        V_Rolle_Gelöscht.objects.using(db_bezeichnung).create(
            v_rolle = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_Rolle_Gelöscht.objects.using(db_bezeichnung).filter(v_rolle = self).latest('zeitstempel').gelöscht

    # V_ROLLE IN DB ANLEGEN
    def in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        # Rolle anlegen
        neue_rolle = Rolle.objects.using(db_bezeichnung_ziel).create(
            zeitstempel = timezone.now()
            )
        neue_rolle.bezeichnung_ändern(db_bezeichnung_ziel, neue_bezeichnung = self.bezeichnung(db_bezeichnung_quelle))
        neue_rolle.entlöschen(db_bezeichnung_ziel)
        # Verbindung zu Vorlage
        Rolle_Vorlage.objects.using(db_bezeichnung_ziel).create(
            rolle = neue_rolle,
            v_rolle_id = self.id
            )
        return neue_rolle

class V_Rolle_Gelöscht(models.Model):
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Rolle_Bezeichnung(models.Model):
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable löschen

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

    # V_WORKFLOW_SCHEMA BEZEICHNUNG
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

    def entlöschen(self, db_bezeichnung):
        V_WFSch_Gelöscht.object.using(db_bezeichnung).create(
            v_wfsch = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_WFSch_Gelöscht.objects.using(db_bezeichnung).filter(v_wfsch = self).latest('zeitstempel').gelöscht

    # V_WORKFLOW_SCHEMA ANFANGSSTUFE
    def anfangsstufe_festlegen(self, db_bezeichnung, v_anfangsstufe):
        V_WFSch_Anfangsstufe.objects.using(db_bezeichnung).create(
            v_wfsch = self,
            v_anfangsstufe = v_anfangsstufe,
            zeitstempel = timezone.now()
            )
    
    def anfangsstufe(self, db_bezeichnung):
        return V_WFSch_Anfangsstufe.objects.using(db_bezeichnung).filter(v_wfsch = self).latest('zeitstempel').v_anfangsstufe
            
    # V_WORKFLOW_SCHEMA IN DB ANLEGEN
    def in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        neues_wfsch = Workflow_Schema.objects.using(db_bezeichnung_ziel).create(
            zeitstempel = timezone.now(),
        )
        neues_wfsch.bezeichnung_ändern(db_bezeichnung_ziel, neue_bezeichnung = self.bezeichnung(db_bezeichnung_quelle))
        neues_wfsch.entlöschen(db_bezeichnung_ziel)
        verbindung_vorlage = WFSch_Vorlage.objects.using(db_bezeichnung_ziel).create(
            wfsch = neues_wfsch,
            v_wfsch_id = self.id
            )
        
        # Anfangsstufe anlegen
        instanz_anfangsstufe = self.anfangsstufe(db_bezeichnung_quelle).in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
        neues_wfsch.anfangsstufe_festlegen(db_bezeichnung_ziel, instanz_anfangsstufe)

        # Nachfolgende Stufen anlegen
        def rekursion_nachfolgende_stufen_anlegen(v_stufe):
            for v_s in v_stufe.liste_folgestufen(db_bezeichnung_quelle):
                # Stufe anlegen
                neue_stufe = v_s.in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
                # Verbindung Folgestufe anlegen
                WFSch_Stufe_Folgestufe.objects.using(db_bezeichnung_ziel).create(
                    wfsch_stufe = v_stufe.instanz(db_bezeichnung_ziel),
                    wfsch_folgestufe = neue_stufe,
                    zeitstempel = timezone.now()
                    )
                rekursion_nachfolgende_stufen_anlegen(v_s)

        rekursion_nachfolgende_stufen_anlegen(self.anfangsstufe(db_bezeichnung_quelle))

class V_WFSch_Gelöscht(models.Model):
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Bezeichnung(models.Model):
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe(models.Model):
    zeitstempel = models.DateTimeField()

    # V_WFSCH_STUFE_BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        V_WFSch_Stufe_Bezeichnung.objects.using(db_bezeichnung).create(
            v_wfsch_stufe = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_WFSch_Stufe_Bezeichnung.objects.using(db_bezeichnung).filter(v_wfsch_stufe = self).latest('zeitstempel').bezeichnung

    # V_WFSCH_STUFE GELÖSCHT
    def löschen(self, db_bezeichnung):
        V_WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).create(
            v_wfsch_stufe = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        V_WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).create(
            v_wfsch_stufe = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).filter(v_wfsch_stufe = self).latest('zeitstempel').gelöscht

    # V_WFSCH_STUFE LISTE FOLGESTUFEN
    def liste_folgestufen(self, db_bezeichnung):
        li_folgestufen = []
        for verbindung_v_fs in V_WFSch_Stufe_Folgestufe.objects.using(db_bezeichnung).filter(v_wfsch_stufe = self):
            if verbindung_v_fs.aktuell(db_bezeichnung) and not verbindung_v_fs.v_wfsch_folgestufe.gelöscht(db_bezeichnung):
                li_folgestufen.append(verbindung_v_fs.v_wfsch_folgestufe)
        return li_folgestufen

    # V_WFSCH_STUFE LISTE ROLLEN
    def liste_rollen(self, db_bezeichnung):
        li_rollen = []
        for verbindung_s_r in V_WFSch_Stufe_Rolle.objects.using(db_bezeichnung).filter(v_wfsch_stufe = self):
            if verbindung_s_r.aktuell(db_bezeichnung) and not verbindung_s_r.v_rolle.gelöscht(db_bezeichnung):
                li_rollen.append(verbindung_s_r.v_rolle)
        return li_rollen

    # V_WFSCH_STUFE IN DB ANLEGEN
    def in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
    # Wird nur für anlegen von WFSCH gebraucht --> Verbindung zu Folgestufen erfolg in Funktion für Anlegn WFSch
        # Stufe anlegen
        neue_wfsch_stufe = WFSch_Stufe.objects.using(db_bezeichnung_ziel).create(
            zeitstempel = timezone.now()
            )
        neue_wfsch_stufe.bezeichnung_ändern(db_bezeichnung_ziel, neue_bezeichnung = self.bezeichnung(db_bezeichnung_quelle))
        neue_wfsch_stufe.entlöschen(db_bezeichnung_ziel)
        # Verbdindung zu Vorlage anlegen
        WFSch_Stufe_Vorlage.objects.using(db_bezeichnung_ziel).create(
            wfsch_stufe = neue_wfsch_stufe,
            v_wfsch_stufe_id = self.id
            )
        # Verbindungen zu Rollen anlegen
        for v_r in self.liste_rollen(db_bezeichnung_quelle):
            # Rolle anlegen wenn nötig
            try:
                rolle = Rolle_Vorlage.objects.using(db_bezeichnung_ziel).get(v_rolle_id = v_r.id).rolle
            except ObjectDoesNotExist:
                rolle = v_r.in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
            # Verbindung zu Rolle anlegen
            verbindung_stufe_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung_ziel).create(
                wfsch_stufe = neue_wfsch_stufe,
                rolle = rolle,
                zeitstempel = timezone.now()
                )
            verbindung_stufe_rolle.aktualisieren(db_bezeichnung_ziel)
        
        # Stufe zurückgeben
        return neue_wfsch_stufe

    def instanz(self, db_bezeichnung):
        return WFSch_Stufe_Vorlage.objects.using(db_bezeichnung).get(v_wfsch_stufe_id = self.id).wfsch_stufe

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
        return V_WFSch_Stufe_Folgestufe_Aktuell.objects.using(db_bezeichnung).filter(v_wfsch_stufe_folgestufe = self).latest('zeitstempel').aktuell

class V_WFSch_Stufe_Folgestufe_Aktuell(models.Model):
    v_wfsch_stufe_folgestufe = models.ForeignKey(V_WFSch_Stufe_Folgestufe, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe_Bezeichnung(models.Model):
    v_wfsch_stufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()

class V_WFSch_Anfangsstufe(models.Model):
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    v_anfangsstufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE)
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

    def ordnerstruktur_in_db_anlegen(self, db_bezeichnung_quelle,  db_bezeichnung_ziel):
        v_o_root = self.root_v_ordner(db_bezeichnung_quelle)
        v_o_root.ordnerbaum_in_db_anlegen(db_bezeichnung_quelle = db_bezeichnung_quelle, db_bezeichnung_ziel = db_bezeichnung_ziel)

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

    def liste_wfsch(self, db_bezeichnung):
        li_wfsch = []
        for verbindung_pjs_wfsch in V_PJS_WFSch.objects.using(db_bezeichnung).filter(v_pjs = self):
            if verbindung_pjs_wfsch.aktuell(db_bezeichnung) and not verbindung_pjs_wfsch.v_wfsch.gelöscht(db_bezeichnung):
                li_wfsch.append(verbindung_pjs_wfsch.v_wfsch)
        return li_wfsch

    def workflowschemata_in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        for wfs in self.liste_wfsch(db_bezeichnung_quelle):
            wfs.in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)

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
#
#
######################################

class Rolle(models.Model):
    zeitstempel = models.DateTimeField()

    # ROLLE BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, *, neue_bezeichnung):
        Rolle_Bezeichnung.objects.using(db_bezeichnung).create(
            rolle = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return Rolle_Bezeichnung.objects.using(db_bezeichnung).filter(rolle = self).latest('zeitstempel').bezeichnung

    # ROLLE LÖSCHEN
    def löschen(self, db_bezeichnung):
        Rolle_Gelöscht.objects.using(db_bezeichnung).create(
            rolle = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        Rolle_Gelöscht.objects.using(db_bezeichnung).create(
            rolle = self, 
            gelöscht = False,
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
    zeitstempel = models.DateTimeField(null = True)  # TODO: Nullable entfernen

class Rolle_Firma(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

class Rolle_Firma_Aktiv(models.Model):
    rolle_firma = models.ForeignKey(Rolle_Firma, on_delete = models.CASCADE)
    aktiv = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Rolle_Vorlage(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    v_rolle_id = models.CharField(max_length = 20)
    # Es soll nur eine Verbindung zur Vorlage geben --> Zeitstempel kann von Rolle übernommen werden

class Workflow_Schema(models.Model):
    bezeichnung = models.CharField(max_length = 50, null = True) # TODO: Feld Löschen
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # WORKFLOW_SCHEMA BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        WFSch_Bezeichnung.objects.using(db_bezeichnung).create(
            wfsch = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return WFSch_Bezeichnung.objects.using(db_bezeichnung).filter(wfsch = self).latest('zeitstempel').bezeichnung

    # WORKFLOW_SCHEMA GELÖSCHT
    def löschen(self, db_bezeichnung):
        WFSch_Gelöscht.objects.using(db_bezeichnung).create(
            wfsch = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        WFSch_Gelöscht.objects.using(db_bezeichnung).create(
            wfsch = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return WFSch_Gelöscht.objects.using(db_bezeichnung).filter(wfsch = self).latest('zeitstempel').gelöscht

    # WORKFLOW_SCHEMA ANFANGSSTUFE
    def anfangsstufe_festlegen(self, db_bezeichnung, anfangsstufe):
        WFSch_Anfangsstufe.objects.using(db_bezeichnung).create(
            wfsch = self,
            anfangsstufe = anfangsstufe,
            zeitstempel = timezone.now()
            )
    
    def anfangsstufe(self, db_bezeichnung):
        return WFSch_Anfangsstufe.objects.using(db_bezeichnung).filter(wfsch = self).latest('zeitstempel').anfangsstufe

class WFSch_Bezeichnung(models.Model):
    wfsch = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class WFSch_Gelöscht(models.Model):
    wfsch = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Vorlage(models.Model):
    wfsch = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    v_wfsch_id = models.CharField(max_length = 20)
 
class WFSch_Stufe(models.Model):
    zeitstempel = models.DateTimeField()

    # WFSCH_STUFE BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        WFSch_Stufe_Bezeichnung.objects.using(db_bezeichnung).create(
            wfsch_stufe = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return WFSch_Bezeichnung.objects.using(db_bezeichnung).filter(wfsch_stufe = self).latest('zeitstempel').bezeichnung

    # WFSCH_STUFE LÖSCHEN
    def löschen(self, db_bezeichnung):
        WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).create(
            wfsch_stufe = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).create(
            wfsch_stufe = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return WFSch_Stufe_Gelöscht.objects.using(db_bezeichnung).filter(wfsch_stufe = self).latest('zeitstempel').gelöscht

class WFSch_Stufe_Gelöscht(models.Model):
    wfsch_stufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Bezeichnung(models.Model):
    wfsch_stufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Folgestufe(models.Model):
    wfsch_stufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE, related_name = 'wfsch_stufe')
    wfsch_folgestufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE, related_name = 'wfsch_folgestufe')
    zeitstempel = models.DateTimeField()

    # WFSCH_STUFE_FOLGESTUFE AKTUELL
    def aktualisieren(self, db_bezeichnung):
        WFSch_Stufe_Folgestufe_Aktuell.objects.using(db_bezeichnung).create(
            wfsch_stufe_folgestufe = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        WFSch_Stufe_Folgestufe_Aktuell.objects.using(db_bezeichnung).create(
            wfsch_stufe_folgestufe = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return WFSch_Stufe_Folgestufe_Aktuell.objects.using(db_bezeichnung).filter(wfsch_stufe_folgestufe = self).lateste('zeitstempel').aktuell

class WFSch_Stufe_Folgestufe_Aktuell(models.Model):
    wfsch_stufe_folgestufe = models.ForeignKey(WFSch_Stufe_Folgestufe, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Anfangsstufe(models.Model):
    wfsch = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    anfangsstufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Rolle(models.Model):
    wfsch_stufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE)
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    # WFSCH_STUFE_ROLLE AKTUELL
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

    # WFSCH_STUFE_ROLLE FIRMEN
    def firma_hinzufügen(self, db_bezeichnung, firma_id):
        verbindung_firma = WFSch_Stufe_Firma.objects.using(db_bezeichnung).get_or_create(
            wfsch_stufe_rolle = self,
            firma_id = firma_id,
            zeitstempel = timezone.now()
            )[0]
        verbindung_firma.aktualisieren(db_bezeichnung)

    def firma_lösen(self, db_bezeichnung, firma_id):
        verbindung_firma = WFSch_Stufe_Firma.objects.using(db_bezeichnung).get(
            wfsch_stufe_rolle = self,
            firma_id = firma_id,
            zeitstempel = timezone.now()
            )
        verbindung_firma.entaktualisieren(db_bezeichnung)

    def liste_firmen_ids(self, db_bezeichnung_firmen, db_bezeichnung):
        li_firmen_ids = []
        for verbindung_firma in WFSch_Stufe_Firma.objects.using(db_bezeichnung).filter(wfsch_stufe_rolle = self):
            firma = Firma.objects.using(db_bezeichnung_firmen).get(pk = verbindung_firma.firma_id)
            if verbindung_firma.aktuell(db_bezeichnung) and not firma.gelöscht:
                li_firmen_ids.append(verbindung_firma.firma_id)#
        return li_firmen_ids
    

class WFSch_Stufe_Rolle_Aktuell(models.Model):
    wfsch_stufe_rolle = models.ForeignKey(WFSch_Stufe_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Firma(models.Model):
    wfsch_stufe_rolle = models.ForeignKey(WFSch_Stufe_Rolle, null = True, on_delete = models.CASCADE) # TODO: Nullable entfernen
    firma_id = models.CharField(max_length=20)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # WFSCH_STUFE_FIRMA AKTUELL
    def aktualisieren(self, db_bezeichnung):
        WFSch_Stufe_Firma_Aktuell.objects.using(db_bezeichnung).create(
            wfsch_stufe_firma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self, db_bezeichnung):
        WFSch_Stufe_Firma_Aktuell.objects.using(db_bezeichnung).create(
            wfsch_stufe_firma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return WFSch_Stufe_Firma_Aktuell.objects.using(db_bezeichnung).filter(wfsch_stufe_firma = self).latest('zeitstempel').aktuell

class WFSch_Stufe_Firma_Aktuell(models.Model):
    wfsch_stufe_firma = models.ForeignKey(WFSch_Stufe_Firma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Mitarbeiter(models.Model):
    immer_erforderlich = models.BooleanField()
    wfsch_stufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE)
    mitarbeiter_id = models.CharField(max_length=20, default='Das ist nicht gültig')
    gelöscht = models.BooleanField(default = False)
    zeitstempel = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return str('%s - %s' % (self.wfsch_stufe.workflow_schema.bezeichnung, self.mitarbeiter.last_name,))

class WFSch_Stufe_Vorlage(models.Model):
    wfsch_stufe = models.ForeignKey(WFSch_Stufe, on_delete = models.CASCADE)
    v_wfsch_stufe_id = models.CharField(max_length = 20)

class Ordner(models.Model):
    # bezeichnung = models.CharField(max_length = 50)
    ist_root_ordner = models.BooleanField(default = False)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.PROTECT, null = True, blank = True)
    
    #######################################
    # Neue Herangehensweise (Funktionen in Models definieren) 06.02.2021

    # ORDNER BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        Ordner_Bezeichnung.objects.using(db_bezeichnung).create(
            ordner = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )
        
    def bezeichnung(self, db_bezeichnung):
        return Ordner_Bezeichnung.objects.using(db_bezeichnung).filter(ordner = self).latest('zeitstempel').bezeichnung

    # ORDNER VERBINDUNG WFSCH
    def verbindung_wfsch_herstellen(self, db_bezeichnung, wfsch):
        verbindung_ordner_wfsch = Ordner_WFSch.objects.using(db_bezeichnung).get_or_create(
            ordner = self,
            wfsch = wfsch,
            defaults = {'zeitstempel': timezone.now()}
            )
        verbindung_ordner_wfsch.aktualisieren(db_bezeichnung)

    def verbindung_wfsch_lösen(self, db_bezeichnung, wfsch):
        verbindung_ordner_wfsch = Ordner_WFSch.objects.using(db_bezeichnung).get(
            ordner = self,
            wfsch = wfsch,
            )
        verbindung_ordner_wfsch.entaktualisieren(db_bezeichnung)

    # ORDNER VERBINDUNG ROLLE
    def verbindung_rolle_herstellen(self, db_bezeichnung, rolle):
        verbindung_ordner_rolle = Ordner_Rolle.objects.using(db_bezeichnung).get_or_create(
            ordner = self,
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )
        verbindung_ordner_rolle.aktualisieren(db_bezeichnung)

    def verbindung_rolle_lösen(self, db_bezeichnung, rolle):
        verbindung_ordner_rolle = Ordner_Rolle.objects.using(db_bezeichnung).get(
            ordner = self,
            rolle = rolle,
            )
        verbindung_ordner_rolle.entaktualisieren(db_bezeichnung)

    # ORDNER LESEFREIGABE ROLLE
    def lesefreigabe_erteilen_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).create(
            ordner_rolle = o_ro,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )
    
    def lesefreigabe_entziehen_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).create(
            ordner_rolle = o_ro,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        return Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).filter(Ordner_Rolle = o_ro).latest('zeitstempel').freigabe_lesen

    # ORDNER UPLOADFREIGABE ROLLE
    def uploadfreigabe_erteilen_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        Freigabe_Upload_Rolle.objects.using(db_bezeichnung).create(
            ordner_rolle = o_ro, 
            freigabe_upload = True, 
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        Freigabe_Upload_Rolle.objects.using(db_bezeichnung).create(
            ordner_rolle = o_ro, 
            freigabe_upload = False, 
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
        return Freigabe_Upload_Rolle.objects.using(db_bezeichnung).filter(ordner_rolle = o_ro).latest('zeitstempel').freigabe_upload

    # ORDNER FREIGABEN VORLAGE
    def vorlage(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        try:
            verbindung_vorlage = Ordner_Vorlage.objects.using(db_bezeichnung_ziel).get(ordner = self)
            return V_Ordner.objects.using(db_bezeichnung_quelle).get(pk = verbindung_vorlage.v_ordner_id)
        except ObjectDoesNotExist:
            return None

    def freigaben_von_vorlage_übernehmen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        v_ordner = self.vorlage(db_bezeichnung_quelle, db_bezeichnung_ziel)
        for v_r in v_ordner.liste_rollen(db_bezeichnung_quelle):
            # Rolle wenn nötig in DB anlegen
            try:
                rolle = Rolle_Vorlage.objects.using(db_bezeichnung_ziel).get(v_rolle_id = v_r.id).rolle
            except ObjectDoesNotExist:
                rolle = v_r.in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
            # Verbindung Ordner Rolle herstellen
            ordner_rolle = Ordner_Rolle.objects.using(db_bezeichnung_ziel).get_or_create(
                ordner = self,
                rolle = rolle,
                defaults = {'zeitstempel':timezone.now()}
                )[0]
            ordner_rolle.aktualisieren(db_bezeichnung_ziel)
            # Freigaben übernehmen
            if v_ordner.freigabe_lesen(db_bezeichnung_quelle, v_rolle = v_r):
                self.lesefreigabe_erteilen_rolle(db_bezeichnung_ziel, rolle = rolle)
            else:
                self.lesefreigabe_entziehen_rolle(db_bezeichnung_ziel, rolle = rolle)
            if v_ordner.freigabe_upload(db_bezeichnung_quelle, v_rolle = v_r):
                self.uploadfreigabe_erteilen_rolle(db_bezeichnung_ziel, rolle = rolle)
            else:
                self.uploadfreigabe_entziehen_rolle(db_bezeichnung_ziel, rolle = rolle)
    
    # ORDNER LESEFREIGABE FIRMA
    def lesefreigabe_erteilen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma = firma)
        Freigabe_Lesen_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_entziehen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma = firma)
        Freigabe_Lesen_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma = firma)
        return Freigabe_Lesen_Firma.objects.using(db_bezeichnung).filter(ordner_firma = o_fa).lateste('zeitstempel').freigabe_lesen

    # ORDNER UPLOADFREIGABE FIRMA
    def uploadfreigabe_erteilen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma = firma)
        Freigabe_Upload_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_upload = True,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma = firma)
        Freigabe_Upload_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    def uploadreigabe_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma = firma)
        return Freigabe_Upload_Firma.objects.using(db_bezeichnung).filter(ordner_firma = o_fa).latest('zeitstempel').freigabe_upload

    # ORDNER UNTERORDNER
    def unterordner_anlegen(self, db_bezeichnung, *, bezeichnung_unterordner):
        neuer_unterordner = Ordner.objects.using(db_bezeichnung).create(
            zeitstempel = timezone.now(),
            ist_root_ordner = False,
            )
        neuer_unterordner.bezeichnung_ändern(db_bezeichnung, bezeichnung_unterordner)
        # Mit "nicht gelöscht" initialisieren
        Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            ordner = neuer_unterordner,
            gelöscht = False,
            zeitstempel = timezone.now()
            )
        # Verbindung Ordner-Unterordner anlegen
        Ordner_Unterordner.objects.using(db_bezeichnung).create(
            ordner = self,
            unterordner = neuer_unterordner,
            zeitstempel = timezone.now()
            )

    # ORDNER LÖSCHEN
    def löschen(self, db_bezeichnung):
    # Verbindungen zu Über-/ Unterordnern werden nicht mitgelöscht, sonst fehlen sie wenn Ordner wieder entlöscht wird
        Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            ordner = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )
            
            # TODO: Prüfen ob Dokumente, Unterordner etc. verknüpft
            # TODO: Unterliegenden Ordnerbaum mitlöschen

    def entlöschen(self, db_bezeichnung):
        Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            ordner = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return Ordner_Gelöscht.objects.using(db_bezeichnung).filter(v_ordner = self).latest('zeitstempel').gelöscht

###################################
# Neue Herangehensweise 08.02.2021

class Ordner_Bezeichnung(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class Ordner_Gelöscht(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ordner_Unterordner(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE, related_name = 'rel_ordner')
    unterordner = models.ForeignKey(Ordner, on_delete = models.CASCADE, related_name = 'rel_unterordner')
    zeitstempel = models.DateTimeField()

    # ORDNER_UNTERORDNER AKTUELL
    def aktualisieren(self, db_bezeichnung):
        Ordner_Unterordner_Aktuell.objects.using(db_bezeichnung).create(
            ordner_unterordner = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        Ordner_Unterordner_Aktuell.objects.using(db_bezeichnung).create(
            ordner_unterordner = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return Ordner_Unterordner_Aktuell.objects.using(db_bezeichnung).filter(ordner_unterordner = self).latest('zeitstempel').aktuell

class Ordner_Unterordner_Aktuell(models.Model):
    ordner_unterordner = models.ForeignKey(Ordner_Unterordner, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ordner_Vorlage(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    v_ordner_id = models.CharField(max_length = 20)
    # Es soll nur eine Verbindung zur Vorlage geben --> Zeitstempel kann von Ordner übernommen werden

#
##################################

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
# Projektstruktur


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

class Projektstruktur(models.Model):
    zeitstempel = models.DateTimeField()
    projektstruktur_id = models.CharField(max_length = 20)
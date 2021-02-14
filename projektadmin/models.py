from datetime import time
from django import db
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.db.models.query_utils import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from superadmin.models import Firma, Projekt_DB
from gernotbau.settings import DB_SUPER
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
        try:
            return V_Ordner_Freigabe_Lesen.objects.using(db_bezeichnung).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_lesen
        except ObjectDoesNotExist:
            return None

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
        try:
            return V_Ordner_Freigabe_Upload.objects.using(db_bezeichnung).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_upload
        except ObjectDoesNotExist:
            return None

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

    # V_ORDNER ROLLEN
    def liste_rollen(self, db_bezeichnung):
        li_v_rollen = []
        for verbindung_o_r in V_Ordner_Rolle.objects.filter(v_ordner = self):
            if verbindung_o_r.aktuell(db_bezeichnung) and not verbindung_o_r.v_rolle.gelöscht(db_bezeichnung):
                li_v_rollen.append(verbindung_o_r.v_rolle)
        return li_v_rollen

    # V_ORDNER ÜBERORDNER
    def überordner(self, db_bezeichnung):
        qs_verbindungen_üo_o = V_Ordner_Unterordner.objects.using(db_bezeichnung).filter(v_unterordner = self)
        if qs_verbindungen_üo_o:
            jüngste_verbindung_üo_o = qs_verbindungen_üo_o.latest('zeitstempel')
            if jüngste_verbindung_üo_o.aktuell(db_bezeichnung) and not jüngste_verbindung_üo_o.v_ordner.gelöscht(db_bezeichnung):
                return jüngste_verbindung_üo_o.v_ordner
        else:
            return None

    # V_ORDNER EBENE
    def ebene(self, db_bezeichnung):
        v_o = self
        ebene = 0
        while v_o.überordner(db_bezeichnung):
            ebene += 1
            v_o = v_o.überordner(db_bezeichnung)
        
        return ebene

    # V_ORDNER IN DB ANLEGEN
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

    def instanz(self, db_bezeichnung_ziel):
        return Ordner_Vorlage.objects.using(db_bezeichnung_ziel).get(v_ordner_id = self.id).ordner

    def ordnerbaum_in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
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
        # Nur anlegen wenn nicht bereits Instanz vorhanden
        if not self.instanz(db_bezeichnung_ziel):
        
            neues_wfsch = Workflow_Schema.objects.using(db_bezeichnung_ziel).create(
                zeitstempel = timezone.now(),
            )
            neues_wfsch.bezeichnung_ändern(db_bezeichnung_ziel, neue_bezeichnung = self.bezeichnung(db_bezeichnung_quelle))
            neues_wfsch.entlöschen(db_bezeichnung_ziel)
            verbindung_vorlage = WFSch_Vorlage.objects.using(db_bezeichnung_ziel).create(
                wfsch = neues_wfsch,
                v_wfsch_id = self.id,
                zeitstempel = timezone.now()
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

    def instanz(self, db_bezeichnung):
        verbindungen_zu_instanzen = WFSch_Vorlage.objects.using(db_bezeichnung).filter(v_wfsch_id = self.id)
        if verbindungen_zu_instanzen and not verbindungen_zu_instanzen.latest('zeitstempel').wfsch.gelöscht(db_bezeichnung):
            jüngste_instanz = verbindungen_zu_instanzen.latest('zeitstempel').wfsch
            if not jüngste_instanz.gelöscht(db_bezeichnung):
                return jüngste_instanz
        # Wenn keine Instanz vorhanden: None zurückgeben
        return None

    # V_WORKFLOW_SCHEMA DICT
    def v_wfsch_dict(self, db_bezeichnung):
        wfsch_d = self.__dict__
        wfsch_d['bezeichnung'] = self.bezeichnung(db_bezeichnung)

        return wfsch_d

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
            v_wfsch_stufe_id = self.id,
            zeitstempel = timezone.now()
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
        verbindungen_zu_instanzen = WFSch_Stufe_Vorlage.objects.using(db_bezeichnung).filter(v_wfsch_stufe_id = self.id)
        if verbindungen_zu_instanzen:
            jüngste_instanz = verbindungen_zu_instanzen.latest('zeitstempel').wfsch_stufe
            if not jüngste_instanz.gelöscht(db_bezeichnung):
                return jüngste_instanz
        # Wenn keine nicht gelöschten Instanzen vorhanden None zurückgeben
        return None

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

    # "Aktuell"-Logik implementiert, obwohl immer nur ein WFSch zugewiesen ist, weil sonst immer ein WFSchn zugewiesen sein muss

    # V_ORDNER_WFSCH AKTUELL
    def aktualisieren(self, db_bezeichnung):
        V_Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        V_Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            v_ordner_wfsch = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return V_Ordner_WFSch_Aktuell.objects.filter(v_ordner_wfsch = self).latest('zeitstempel').aktuell

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

    # V_PJS GELÖSCHT
    def löschen(self, db_bezeichnung):
        V_PJS_Gelöscht.objects.using(db_bezeichnung).create(
            v_pjs = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        V_PJS_Gelöscht.objects.using(db_bezeichnung).create(
            v_pjs = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return V_PJS_Gelöscht.objects.using(db_bezeichnung).filter(v_pjs = self).latest('zeitstempel').gelöscht

    # V_PJS BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, bezeichnung):
        V_PJS_Bezeichnung.objects.using(db_bezeichnung).create(
            v_pjs = self,
            bezeichnung = bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return V_PJS_Bezeichnung.objects.using(db_bezeichnung).filter(v_pjs = self).latest('zeitstempel').bezeichnung

    # V_PJS ORDNER
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

    def liste_verbindungen_ordner_wfsch(self, db_bezeichnung):
        li_verbindungen_o_wfsch = []
        for v_o in self.liste_ordner(db_bezeichnung):
            try:
                verbindung_o_wfsch = V_Ordner_WFSch.objects.filter(v_ordner = v_o).latest('zeitstempel')
                li_verbindungen_o_wfsch.append(verbindung_o_wfsch)
            except ObjectDoesNotExist:
                pass
        return li_verbindungen_o_wfsch

    def root_v_ordner(self, db_bezeichnung):
        for v_pjs_o in V_PJS_Ordner.objects.using(db_bezeichnung).filter(v_pjs = self):
            if v_pjs_o.aktuell(db_bezeichnung):
                v_o = v_pjs_o.v_ordner
                if v_o.ist_root_ordner and not v_o.gelöscht(db_bezeichnung):
                    return v_o

    def ordnerstruktur_in_db_anlegen(self, db_bezeichnung_quelle,  db_bezeichnung_ziel):
        for oberster_v_o in liste_oberste_v_ordner(db_bezeichnung_quelle):
            oberster_v_o.ordnerbaum_in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)

    # V_PJS WFSCH
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
        for wfsch in self.liste_wfsch(db_bezeichnung_quelle):
            wfsch.in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)

    # V_PJS ROLLEN
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

    # V_PJS DICT
    def v_pjs_dict(self, db_bezeichnung):
        dict_pjs = self.__dict__
        dict_pjs['bezeichnung'] = self.bezeichnung(db_bezeichnung)

        return dict_pjs

    # V_PJS AUF PROJEKT ÜBERTRAGEN
    def in_db_anlegen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        Projektstruktur.objects.using(db_bezeichnung_ziel).create(
            v_pjs_id = self.id,
            zeitstempel = timezone.now()
            )
        self.ordnerstruktur_in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
        self.workflowschemata_in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
        
        # Verbindungen Ordner-WFSch anlegen
        for verbindung_o_wfsch in self.liste_verbindungen_ordner_wfsch(db_bezeichnung_quelle):
            instanz_verbindung_o_wfsch = Ordner_WFSch.objects.using(db_bezeichnung_ziel).create(
                ordner = verbindung_o_wfsch.v_ordner.instanz(db_bezeichnung_ziel),
                wfsch = verbindung_o_wfsch.v_wfsch.instanz(db_bezeichnung_ziel),
                zeitstempel = timezone.now()
                )
            instanz_verbindung_o_wfsch.aktualisieren(db_bezeichnung_ziel)

class V_PJS_Gelöscht(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_PJS_Bezeichnung(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
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

class V_PJS_Rolle_Aktuell(models.Model):
    v_pjs_rolle = models.ForeignKey(V_PJS_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
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
        return Rolle_Gelöscht.objects.using(db_bezeichnung).filter(rolle = self).latest('zeitstempel').gelöscht

    # ROLLE FIRMA
    def firma_zuweisen(self, db_bezeichnung, firma):
        neue_verbindung_r_f = Rolle_Firma.objects.using(db_bezeichnung).get_or_create(
            rolle = self,
            firma_id = firma.id, 
            defaults = {'zeitstempel':timezone.now()}
            )[0]
        neue_verbindung_r_f.aktualisieren(db_bezeichnung)

    def ist_firmenrolle(self, db_bezeichnung, firma):
        # Prüfen ob Verbindung Rolle-Firma aktuell
        try:
            verbindung_r_fa = Rolle_Firma.objects.using(db_bezeichnung).get(rolle = self, firma_id = firma.id)
            if verbindung_r_fa.aktuell(db_bezeichnung):
                return True
            else:
                return False
        # Wenn keine Vebindung Rolle-Firam: False zurückgeben
        except ObjectDoesNotExist:
            return False

    def ist_firmenrolle_ändern(self, db_bezeichnung, firma, ist_firmenrolle):
        verbindung_r_fa = Rolle_Firma.objects.using(db_bezeichnung).get_or_create(
            rolle = self,
            firma_id = firma.id,
            defaults = {'zeitstempel':timezone.now()}
            )[0]

        if ist_firmenrolle == True:
            verbindung_r_fa.aktualisieren(db_bezeichnung)
        else:
            verbindung_r_fa.entaktualisieren(db_bezeichnung)

    # ROLLE DICT
    def dict_rolle(self, db_bezeichnung):
        rolle_d = self.__dict__
        rolle_d['bezeichnung'] = self.bezeichnung(db_bezeichnung)

        return rolle_d

    # ROLLE FREIGABEN AUF FIRMA ÜBERTRAGEN
    def freigaben_übertragen_firma(self, db_bezeichnung, firma):
        for o in liste_ordner(db_bezeichnung):
            if o.lesefreigabe_rolle(db_bezeichnung, self) and not o.lesefreigabe_firma(db_bezeichnung, firma):
                o.lesefreigabe_erteilen_firma(db_bezeichnung, firma)
            if o.uploadfreigabe_rolle(db_bezeichnung, self) and not o.uploadfreigabe_firma(db_bezeichnung, firma):
                o.uploadfreigabe_erteilen_firma(db_bezeichnung, firma)

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

    # ROLLE_FIRMA AKTUELL
    def aktualisieren(self, db_bezeichnung):
        Rolle_Firma_Aktuell.objects.using(db_bezeichnung).create(
            rolle_firma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        Rolle_Firma_Aktuell.objects.using(db_bezeichnung).create(
            rolle_firma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return Rolle_Firma_Aktuell.objects.using(db_bezeichnung).filter(rolle_firma = self).latest('zeitstempel').aktuell

class Rolle_Firma_Aktuell(models.Model):
    rolle_firma = models.ForeignKey(Rolle_Firma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Rolle_Vorlage(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    v_rolle_id = models.CharField(max_length = 20)
    # Es soll nur eine Verbindung zur Vorlage geben --> Zeitstempel kann von Rolle übernommen werden

class Workflow_Schema(models.Model):
    # bezeichnung = models.CharField(max_length = 50, null = True) # TODO: Feld Löschen
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
        
        # Stufen löschen
        stufe = self.anfangsstufe(db_bezeichnung)
        while stufe:
            stufe.löschen(db_bezeichnung)
            stufe = stufe.folgestufe(db_bezeichnung)
            
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

    def letzte_stufe(self, db_bezeichnung):
        # Letzte Stufe ist die Stufe ohne Folgestufe
        for s in self.liste_stufen(db_bezeichnung):
            if not s.folgestufe(db_bezeichnung):
                return s

    # WORKFLOW_SCHEMA STUFEN
    def stufe_hinzufügen(self, db_bezeichnung, bezeichnung_stufe):
        # Neue Stufe anlegen
        neue_wfsch_stufe = WFSch_Stufe.objects.using(db_bezeichnung).create(
            zeitstempel = timezone.now()
            )
        neue_wfsch_stufe.entlöschen(db_bezeichnung)
        neue_wfsch_stufe.bezeichnung_ändern(db_bezeichnung, neue_bezeichnung = bezeichnung_stufe)
        # Neue Stufe wird Folgestufe von bisheriger letzter Stufe
        self.letzte_stufe(db_bezeichnung).folgestufe_festlegen(db_bezeichnung, neue_wfsch_stufe)

    def liste_stufen(self, db_bezeichnung):
        stufe = self.anfangsstufe(db_bezeichnung)
        li_stufen = []
        while stufe:
            li_stufen.append(stufe)
            stufe = stufe.folgestufe(db_bezeichnung)
        return li_stufen
    
    def liste_stufen_dict(self, db_bezeichnung_quelle, db_bezeichnung_ziel, projekt):
        li_stufen_dict = []
        for s in self.liste_stufen(db_bezeichnung_ziel):
            li_stufen_dict.append(s.wfsch_stufe_dict(db_bezeichnung_quelle, db_bezeichnung_ziel, projekt))
        return li_stufen_dict

    # WORKFLOW_SCHEMA DICT
    def wfsch_dict(self, db_bezeichnung_quelle, db_bezeichnung_ziel, projekt):
        wfsch_dict = self.__dict__
        wfsch_dict['bezeichnung'] = self.bezeichnung(db_bezeichnung_ziel)
        wfsch_dict['liste_wfsch_stufen'] = self.liste_stufen_dict(db_bezeichnung_quelle, db_bezeichnung_ziel, projekt)

        return wfsch_dict

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
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

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
        return WFSch_Stufe_Bezeichnung.objects.using(db_bezeichnung).filter(wfsch_stufe = self).latest('zeitstempel').bezeichnung

    # WFSCH_STUFE FOLGESTUFE
    def folgestufe_festlegen(self, db_bezeichnung, folgestufe):
        WFSch_Stufe_Folgestufe.objects.using(db_bezeichnung).create(
            wfsch_stufe = self,
            wfsch_folgestufe = folgestufe,
            zeitstempel = timezone.now()
            )
    
    def folgestufe(self, db_bezeichnung):
        qs_verbindungen_s_fs = WFSch_Stufe_Folgestufe.objects.using(db_bezeichnung).filter(wfsch_stufe = self)
        # Wenn keine Folgestufe: None zurückgeben
        if qs_verbindungen_s_fs:
            fs = qs_verbindungen_s_fs.latest('zeitstempel').wfsch_folgestufe
            if not fs.gelöscht(db_bezeichnung):
                return qs_verbindungen_s_fs.latest('zeitstempel').wfsch_folgestufe
            else:
                return None
        else:
            return None

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

    # WFSCH_STUFE ROLLEN
    def rolle_hinzufügen(self, db_bezeichnung, rolle):
        verbindung_wfsch_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung).create(
            wfsch_stufe = self,
            rolle = rolle,
            zeitstempel = timezone.now()
            )
        verbindung_wfsch_rolle.aktualisieren(db_bezeichnung)

    def rolle_lösen(self, db_bezeichnung, rolle):
        verbindung_wfsch_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung).get(
            wfsch_stufe = self,
            rolle = rolle
            )
        verbindung_wfsch_rolle.entaktualisieren(db_bezeichnung)

    def liste_rollen(self, db_bezeichnung):
        li_rollen = []
        for verbindung_wfschSt_r in WFSch_Stufe_Rolle.objects.using(db_bezeichnung).filter(wfsch_stufe = self):
            if verbindung_wfschSt_r.aktuell(db_bezeichnung) and not verbindung_wfschSt_r.rolle.gelöscht(db_bezeichnung):
                li_rollen.append(verbindung_wfschSt_r.rolle)
        return li_rollen

    def liste_rollen_dict(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        li_rollen_dict= []
        for r in self.liste_rollen(db_bezeichnung_ziel):
            rolle_dict = r.__dict__
            rolle_dict['bezeichnung'] = r.bezeichnung(db_bezeichnung_ziel)
            verbindung_wfsch_stufe_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung_ziel).get(wfsch_stufe = self, rolle = r)
            rolle_dict['liste_prüffirmen'] = verbindung_wfsch_stufe_rolle.liste_firmen_dict(db_bezeichnung_quelle, db_bezeichnung_ziel)
            
            li_rollen_dict.append(rolle_dict)
        return li_rollen_dict

    # WFSCH_STUFE FIRMEN
    def prüffirma_hinzufügen(self, db_bezeichnung, rolle, firma_id):
        verbindung_wfschSt_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung).get(wfsch_stufe = self, rolle = rolle)
        verbindung_wfschSt_firma = WFSch_Stufe_Firma.objects.using(db_bezeichnung).get_or_create(
            wfsch_stufe_rolle = verbindung_wfschSt_rolle, 
            firma_id = firma_id,
            defaults = {'zeitstempel':timezone.now()}
            )[0]
        verbindung_wfschSt_firma.aktualisieren(db_bezeichnung)

    def prüffirma_lösen(self, db_bezeichnung, rolle, firma_id):
        verbindung_wfschSt_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung).get(wfsch_stufe = self, rolle = rolle)
        verbindung_wfschSt_firma = WFSch_Stufe_Firma.objects.using(db_bezeichnung).get(
            wfsch_stufe_rolle = verbindung_wfschSt_rolle,
            firma_id = firma_id
            )
        verbindung_wfschSt_firma.entaktualisieren(db_bezeichnung)

    def liste_prüffirmen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        li_prüffirmen = []
        for r in self.liste_rollen(db_bezeichnung_ziel):
            verbindung_wfschSt_rolle = WFSch_Stufe_Rolle.objects.using(db_bezeichnung_ziel).get(wfsch_stufe = self, rolle = r)
            for fa in verbindung_wfschSt_rolle.liste_firmen(db_bezeichnung_quelle, db_bezeichnung_ziel):
                if not fa in li_prüffirmen:
                    li_prüffirmen.append(fa)
        return li_prüffirmen

    def liste_nicht_prüffirmen(self, db_bezeichnung_quelle, db_bezeichnung_ziel, projekt):
        li_nicht_prüffirmen = []
        for fa in projekt.liste_projektfirmen(db_bezeichnung_quelle):
            if fa not in self.liste_prüffirmen(db_bezeichnung_quelle, db_bezeichnung_ziel):
                li_nicht_prüffirmen.append(fa)
        return li_nicht_prüffirmen 

    def liste_nicht_prüffirmen_dict(self, db_bezeichnung_quelle, db_bezeichnung_ziel, projekt):
        li_nicht_pf_dict = []
        for pf in self.liste_nicht_prüffirmen(db_bezeichnung_quelle, db_bezeichnung_ziel, projekt):
            li_nicht_pf_dict.append(pf.firma_dict(db_bezeichnung_quelle))
        return li_nicht_pf_dict

    # WFSCH_STUFE DICT

    def wfsch_stufe_dict(self, db_bezeichnung_quelle, db_bezeichnung_ziel, projekt):
        wfsch_s_dict = self.__dict__
        wfsch_s_dict['liste_nicht_prüffirmen'] = self.liste_nicht_prüffirmen_dict(db_bezeichnung_quelle, db_bezeichnung_ziel, projekt)
        wfsch_s_dict['liste_rollen'] = self.liste_rollen_dict(db_bezeichnung_quelle, db_bezeichnung_ziel)
        wfsch_s_dict['bezeichnung'] = self.bezeichnung(db_bezeichnung_ziel)

        return wfsch_s_dict

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

    # Dzt. so ausgelegt, dass es immer nur eine Folgestufe gibt --> akutalisieren/entaktualisieren nicht erforderlich
    
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

    def liste_firmen(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        li_firmen = []
        for verbindung_firma in WFSch_Stufe_Firma.objects.using(db_bezeichnung_ziel).filter(wfsch_stufe_rolle = self):
            firma = Firma.objects.using(db_bezeichnung_quelle).get(pk = verbindung_firma.firma_id)
            if verbindung_firma.aktuell(db_bezeichnung_ziel) and not firma.gelöscht(db_bezeichnung_quelle):
                li_firmen.append(firma)
        return li_firmen
    
    def liste_firmen_dict(self, db_bezeichnung_quelle, db_bezeichnung_ziel):
        li_firmen_dict = []
        for fa in self.liste_firmen(db_bezeichnung_quelle, db_bezeichnung_ziel):
            li_firmen_dict.append(fa.firma_dict(db_bezeichnung_quelle))
        return li_firmen_dict

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
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

class Ordner(models.Model):
    # bezeichnung = models.CharField(max_length = 50)
    ist_root_ordner = models.BooleanField(default = False)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen
    
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
            )[0]
        verbindung_ordner_wfsch.aktualisieren(db_bezeichnung)

    def verbindung_wfsch_löschen(self, db_bezeichnung):
        try:
            verbindung_ordner_wfsch = Ordner_WFSch.objects.using(db_bezeichnung).filter(ordner = self).latest('zeitstempel')
            verbindung_ordner_wfsch.entaktualisieren(db_bezeichnung)
        except ObjectDoesNotExist:
            pass

    def wfsch(self, db_bezeichnung):
        try:
            verbindung_o_wfsch = Ordner_WFSch.objects.using(db_bezeichnung).filter(ordner = self).latest('zeitstempel')
            if verbindung_o_wfsch.aktuell(db_bezeichnung) and not verbindung_o_wfsch.wfsch.gelöscht(db_bezeichnung):
                return verbindung_o_wfsch.wfsch
        except ObjectDoesNotExist:
            return None

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
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get_or_create(
            ordner = self, 
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
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
        try:
            o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
            return Freigabe_Lesen_Rolle.objects.using(db_bezeichnung).filter(ordner_rolle = o_ro).latest('zeitstempel').freigabe_lesen
        except ObjectDoesNotExist:
            return False

    # ORDNER UPLOADFREIGABE ROLLE
    def uploadfreigabe_erteilen_rolle(self, db_bezeichnung, rolle):
        o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get_or_create(
            ordner = self, 
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
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
        try:
            o_ro = Ordner_Rolle.objects.using(db_bezeichnung).get(ordner = self, rolle = rolle)
            return Freigabe_Upload_Rolle.objects.using(db_bezeichnung).filter(ordner_rolle = o_ro).latest('zeitstempel').freigabe_upload
        except ObjectDoesNotExist:
            return False

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
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get_or_create(
            ordner = self, 
            firma_id = firma.id,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        Freigabe_Lesen_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )
        # Uploadfreigabe entziehen (gleichzeitige Lese- und Uploadfreigabe vermeiden)
        Freigabe_Upload_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_entziehen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma_id = firma.id)
        Freigabe_Lesen_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_firma(self, db_bezeichnung, firma):
        try:
            o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma_id = firma.id)
            return Freigabe_Lesen_Firma.objects.using(db_bezeichnung).filter(ordner_firma = o_fa).latest('zeitstempel').freigabe_lesen
        except ObjectDoesNotExist:
            return False

    # ORDNER UPLOADFREIGABE FIRMA
    def uploadfreigabe_erteilen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get_or_create(
            ordner = self, 
            firma_id = firma.id,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        Freigabe_Upload_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_upload = True,
            zeitstempel = timezone.now()
            )
        # Lesefreigabe entziehen (gleichzeitige Lese- und Uploadfreigabe vermeiden)
        Freigabe_Lesen_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen_firma(self, db_bezeichnung, firma):
        o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma_id = firma.id)
        Freigabe_Upload_Firma.objects.using(db_bezeichnung).create(
            ordner_firma = o_fa,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_firma(self, db_bezeichnung, firma):
        try:
            o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma_id = firma.id)
            return Freigabe_Upload_Firma.objects.using(db_bezeichnung).filter(ordner_firma = o_fa).latest('zeitstempel').freigabe_upload
        except ObjectDoesNotExist:
            return False

    # ORDNER ALLE FREIGABEN
    def freigaben_übertragen_rollen_firma(self, db_bezeichnung, firma):
        self.freigaben_entziehen_firma(db_bezeichnung, firma)
        for rolle in liste_rollen_firma(db_bezeichnung, firma):
            if self.lesefreigabe_rolle(db_bezeichnung, rolle) and not self.lesefreigabe_firma(db_bezeichnung, firma) and not self.uploadfreigabe_firma(db_bezeichnung, firma):
                self.lesefreigabe_erteilen_firma(db_bezeichnung, firma)
            if self.uploadfreigabe_rolle(db_bezeichnung, rolle) and not self.uploadfreigabe_firma(db_bezeichnung, firma):
                self.uploadfreigabe_erteilen_firma(db_bezeichnung, firma)
    
    def freigaben_entziehen_firma(self, db_bezeichnung, firma):
        try:
            o_fa = Ordner_Firma.objects.using(db_bezeichnung).get(ordner = self, firma_id = firma.id)
            Freigabe_Lesen_Firma.objects.using(db_bezeichnung).create(
                ordner_firma = o_fa,
                freigabe_lesen = False,
                zeitstempel = timezone.now()
                )
            Freigabe_Upload_Firma.objects.using(db_bezeichnung).create(
                ordner_firma = o_fa,
                freigabe_upload = False,
                zeitstempel = timezone.now()
                )        
        except ObjectDoesNotExist:
            pass

    # ORDNER UNTERORDNER
    def unterordner_anlegen(self, db_bezeichnung, bezeichnung_unterordner):
        neuer_unterordner = Ordner.objects.using(db_bezeichnung).create(
            zeitstempel = timezone.now(),
            ist_root_ordner = False,
            )
        neuer_unterordner.bezeichnung_ändern(db_bezeichnung, bezeichnung_unterordner)
        neuer_unterordner.entlöschen(db_bezeichnung)
        # Verbindung Ordner-Unterordner anlegen
        self.unterordner_verbinden(db_bezeichnung, neuer_unterordner)

    def unterordner_verbinden(self, db_bezeichnung, unterordner):
        verbindung_o_uo = Ordner_Unterordner.objects.using(db_bezeichnung).create(
            ordner = self,
            unterordner = unterordner,
            zeitstempel = timezone.now()
            )
        verbindung_o_uo.aktualisieren(db_bezeichnung)

    def liste_unterordner(self, db_bezeichnung):
        qs_verbindungen_o_uo = Ordner_Unterordner.objects.using(db_bezeichnung).filter(ordner = self)
        li_unterordner = []
        for verbindung_o_uo in qs_verbindungen_o_uo:
            if verbindung_o_uo.aktuell(db_bezeichnung) and not verbindung_o_uo.unterordner.gelöscht(db_bezeichnung):
                li_unterordner.append(verbindung_o_uo.unterordner)
        return li_unterordner

    # ORDNER ÜBERORDNER
    def überordner(self, db_bezeichnung):
        qs_verbindungen_üo_o = Ordner_Unterordner.objects.using(db_bezeichnung).filter(unterordner = self)
        if qs_verbindungen_üo_o:
            jüngste_verbindung_üo_o = qs_verbindungen_üo_o.latest('zeitstempel')
            if jüngste_verbindung_üo_o.aktuell(db_bezeichnung) and not jüngste_verbindung_üo_o.ordner.gelöscht(db_bezeichnung):
                return jüngste_verbindung_üo_o.ordner
        else:
            return None

    # ORDNER EBENE
    def ebene(self, db_bezeichnung):
        o = self
        ebene = 0
        while o.überordner(db_bezeichnung):
            ebene += 1
            o = o.überordner(db_bezeichnung)
        return ebene

    # ORDNER LÖSCHEN
    def löschen(self, db_bezeichnung):
    # Verbindungen zu Über-/ Unterordnern werden nicht mitgelöscht, sonst fehlen sie wenn Ordner wieder entlöscht wird
        # Ornder löschen
        Ordner_Gelöscht.objects.using(db_bezeichnung).create(
                    ordner = self,
                    gelöscht = True, 
                    zeitstempel = timezone.now()
                    )
        # Unterliegenden Ordnerbaum mitlöschen
        def rekursion_ordnerbaum_löschen(ordner):
            for uo in ordner.liste_unterordner(db_bezeichnung):
                rekursion_ordnerbaum_löschen(uo)
                Ordner_Gelöscht.objects.using(db_bezeichnung).create(
                    ordner = uo,
                    gelöscht = True, 
                    zeitstempel = timezone.now()
                    )
        
        rekursion_ordnerbaum_löschen(self)
        # TODO: Prüfen ob Dokumente, Unterordner etc. verknüpft
        # TODO: Unterliegenden Ordnerbaum mitlöschen

    def entlöschen(self, db_bezeichnung):
        Ordner_Gelöscht.objects.using(db_bezeichnung).create(
            ordner = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return Ordner_Gelöscht.objects.using(db_bezeichnung).filter(ordner = self).latest('zeitstempel').gelöscht

    def ordner_dict(self,db_super, db_projekt):
        dict_o = self.__dict__
        dict_o['bezeichnung'] = self.bezeichnung(db_projekt)
        wfsch = self.wfsch(db_projekt)
        dict_o['wfsch'] = wfsch.wfsch_dict(db_bezeichnung_quelle = db_super, db_bezeichnung_ziel = db_projekt, projekt = projekt(db_projekt)) if wfsch else None
        
        # Ordnerebene (oberste Ebene, also die direkt unter ROOT-Ordner, ist Ebene '0')
        ebene = 0
        o = self
        while o.überordner(db_projekt):
            ebene += 1
            o = o.überordner(db_projekt)

        dict_o['ebene'] = ebene
        dict_o['vorlage'] = self.vorlage(db_super, db_projekt)

        return dict_o

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
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

class Freigabe_Lesen_Firma(models.Model):
    ordner_firma = models.ForeignKey(Ordner_Firma, on_delete = models.CASCADE)
    freigabe_lesen = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Freigabe_Upload_Firma(models.Model):
    ordner_firma = models.ForeignKey(Ordner_Firma, on_delete = models.CASCADE)
    freigabe_upload = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ordner_WFSch(models.Model):
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    wfsch = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    # "Aktuell"-Logik implementiert, obwohl immer nur ein WFSch zugewiesen ist, weil sonst immer ein WFSchn zugewiesen sein muss

    def aktualisieren(self, db_bezeichnung):
        Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            ordner_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        Ordner_WFSch_Aktuell.objects.using(db_bezeichnung).create(
            ordner_wfsch = self,
            aktuell = False,
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
    v_pjs_id = models.CharField(max_length = 20)

###################################################################
# FUNKTIONEN OHNE KLASSE

# ROLLEN

def liste_rollen(db_bezeichnung):
    li_rollen = []
    for r in Rolle.objects.using(db_bezeichnung).all():
        if not r.gelöscht(db_bezeichnung):
            li_rollen.append(r)
    return li_rollen

def liste_rollen_dict(db_bezeichnung):
    li_rollen_dict = []
    for r in liste_rollen(db_bezeichnung):
        li_rollen_dict.append(r.dict_rolle(db_bezeichnung))
    return li_rollen_dict

def liste_rollen_firma(db_bezeichnung, firma):
    qs_verbindungen_rolle_firma = Rolle_Firma.objects.using(db_bezeichnung).filter(firma_id = firma.id)
    li_rollen_firma = []
    for verbindung_rolle_firma in qs_verbindungen_rolle_firma:
        if verbindung_rolle_firma.aktuell(db_bezeichnung) and not verbindung_rolle_firma.rolle.gelöscht(db_bezeichnung):
            li_rollen_firma.append(verbindung_rolle_firma.rolle)
    return li_rollen_firma

def liste_rollen_firma_dict(db_bezeichnung, firma):
    li_rollen_firma_dicts = []
    for r in liste_rollen_firma(db_bezeichnung, firma):
        li_rollen_firma_dicts.append(r.dict_rolle(db_bezeichnung))
    return li_rollen_firma_dicts

def liste_oberste_ordner(db_bezeichnung):
    li_oberste_o = []
    for o in Ordner.objects.using(db_bezeichnung).all():
        if o.ebene(db_bezeichnung) == 0 and not o.gelöscht(db_bezeichnung):
            li_oberste_o.append(o)
    return li_oberste_o

def liste_oberste_v_ordner(db_bezeichnung):
    li_oberste_v_o = []
    for v_o in V_Ordner.objects.using(db_bezeichnung).all():
        if v_o.ebene(db_bezeichnung) == 0 and not v_o.gelöscht(db_bezeichnung):
            li_oberste_v_o.append(v_o)
    return li_oberste_v_o

# ORDNER
def liste_ordner(db_bezeichnung):
    # Ordnerliste, sortiert nach Ordnerbaum
    li_ordner = []
    def rekursion_uo_anhängen(o):
        for uo in o.liste_unterordner(db_bezeichnung):
            li_ordner.append(uo)
            rekursion_uo_anhängen(uo)
    
    for oberster_ordner in liste_oberste_ordner(db_bezeichnung):
        li_ordner.append(oberster_ordner)
        rekursion_uo_anhängen(oberster_ordner)

    return li_ordner

def liste_ordner_dict(db_super, db_projekt):
    li_ordner_dict = []
    for o in liste_ordner(db_projekt):
        li_ordner_dict.append(o.ordner_dict(db_super, db_projekt))
    return li_ordner_dict

# WFSCH
def liste_wfsch(db_bezeichnung):
    li_wfsch = []
    for wfsch in Workflow_Schema.objects.using(db_bezeichnung).all():
        if not wfsch.gelöscht(db_bezeichnung):
            li_wfsch.append(wfsch)
    return li_wfsch

def liste_wfsch_dict(db_bezeichnung):
    li_wfsch_dict = []
    for wfsch in liste_wfsch(db_bezeichnung):
        li_wfsch_dict.append(wfsch.wfsch_dict(db_bezeichnung_quelle = DB_SUPER, db_bezeichnung_ziel = db_bezeichnung, projekt = projekt(db_bezeichnung)))
    return li_wfsch_dict

# PJS
def liste_v_pjs(db_bezeichnung):
    li_v_pjs = []
    for v_pjs in V_Projektstruktur.objects.using(db_bezeichnung).all():
        if not v_pjs.gelöscht(db_bezeichnung): 
            li_v_pjs.append(v_pjs)
    return li_v_pjs

def liste_v_pjs_dict(db_bezeichnung):
    li_v_pjs_dict = []
    for v_pjs in liste_v_pjs(db_bezeichnung):
        li_v_pjs_dict.append(v_pjs.v_pjs_dict(db_bezeichnung))
    return li_v_pjs_dict

def projekt(db_bezeichnung):
    db_bezeichnung_projekt = Projekt_DB.objects.using(DB_SUPER).filter(db_bezeichnung = db_bezeichnung).latest('zeitstempel')
    if not db_bezeichnung_projekt.projekt.gelöscht(DB_SUPER):
        projekt = db_bezeichnung_projekt.projekt
    return projekt

#
###################################################################

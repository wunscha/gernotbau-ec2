from datetime import time
from django import db
from django.db import models
from django.db.models.fields.related import OneToOneField, create_many_to_many_intermediary_model
from django.db.models.query_utils import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model

from superadmin.models import Mitarbeiter, Projekt, Firma, Projekt_DB
from gernotbau.settings import DB_SUPER
######################################
# VORLAGEN
#
#

class V_Ordner(models.Model):
    zeitstempel = models.DateTimeField()
    ist_root_ordner = models.BooleanField()

    # V_ORDNER BEZEICHNUNG
    def bezeichnung(self):
        return V_Ordner_Bezeichnung.objects.using(DB_SUPER).filter(v_ordner = self).latest('zeitstempel').bezeichnung

    def bezeichnung_ändern(self, neue_bezeichnung):
        V_Ordner_Bezeichnung.objects.using(DB_SUPER).create(
            v_ordner = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    # V_ORDNER FREIGABE LESEN
    def freigabe_lesen(self, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(DB_SUPER).get(v_ordner = self, v_rolle = v_rolle)
        try:
            return V_Ordner_Freigabe_Lesen.objects.using(DB_SUPER).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_lesen
        except ObjectDoesNotExist:
            return None

    def lesefreigabe_erteilen(self, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(DB_SUPER).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Lesen.objects.using(DB_SUPER).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_entziehen(self, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(DB_SUPER).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Lesen.objects.using(DB_SUPER).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    # V_ORDNER FREIGABE UPLOAD
    def freigabe_upload(self, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(DB_SUPER).get(v_ordner = self, v_rolle = v_rolle)
        try:
            return V_Ordner_Freigabe_Upload.objects.using(DB_SUPER).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_upload
        except ObjectDoesNotExist:
            return None

    def uploadfreigabe_erteilen(self, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(DB_SUPER).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Upload.objects.using(DB_SUPER).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_upload = True,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen(self, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(DB_SUPER).get(v_ordner = self, v_rolle = v_rolle)
        V_Ordner_Freigabe_Upload.objects.using(DB_SUPER).create(
            v_ordner_rolle = v_ordner_rolle,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    # V_ORDNER UNTERORDNER
    def unterordner_anlegen(self, bezeichnung_unterordner):
        neuer_unterordner = V_Ordner.objects.using(DB_SUPER).create(
            zeitstempel = timezone.now(),
            ist_root_ordner = False,
            )
        neuer_unterordner.bezeichnung_ändern(bezeichnung_unterordner)
        # Mit "nicht gelöscht" initialisieren
        V_Ordner_Gelöscht.objects.using(DB_SUPER).create(
            v_ordner = neuer_unterordner,
            gelöscht = False,
            zeitstempel = timezone.now()
            )
        # Verbindung Ordner-Unterordner anlegen
        neue_verbindung_ordner_unterordner = V_Ordner_Unterordner.objects.using(DB_SUPER).create(
            v_ordner = self,
            v_unterordner = neuer_unterordner,
            zeitstempel = timezone.now()
            )
        neue_verbindung_ordner_unterordner.aktualisieren()

    def liste_unterordner(self):
    # Gibt Liste der aktuellen Unterordner zurück
        qs_v_ordner_unterordner = V_Ordner_Unterordner.objects.using(DB_SUPER).filter(v_ordner = self)
        li_unterordner = []
        for e in qs_v_ordner_unterordner:
            if e.aktuell() and not e.v_unterordner.gelöscht(): li_unterordner.append(e.v_unterordner)
        return li_unterordner

    # V_ORDNER LÖSCHEN
    def löschen(self):
        V_Ordner_Gelöscht.objects.using(DB_SUPER).create(
            v_ordner = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )
        # Verbindung zu Überordner lösen
        verbindung_zu_überordner = V_Ordner_Unterordner.objects.using(DB_SUPER).get(unterordner = self)
        verbindung_zu_überordner.entaktualisieren()
        # Verbindungen zu Unterordnern lösen
        # TODO: Gesamter Baum unterhalb Ordner sollte gelöscht werden (Ordner und Verbindungen)
        for uo in self.liste_unterordner():
            verbindung_zu_unterordner = V_Ordner_Unterordner.objects.using(DB_SUPER).get(unterordner = uo)
            verbindung_zu_unterordner.entaktualisieren()

    def gelöscht(self):
        return V_Ordner_Gelöscht.objects.using(DB_SUPER).filter(v_ordner = self).latest('zeitstempel').gelöscht

    # V_ORDNER ROLLEN
    def liste_rollen(self):
        li_v_rollen = []
        for verbindung_o_r in V_Ordner_Rolle.objects.filter(v_ordner = self):
            if verbindung_o_r.aktuell() and not verbindung_o_r.v_rolle.gelöscht():
                li_v_rollen.append(verbindung_o_r.v_rolle)
        return li_v_rollen

    # V_ORDNER ÜBERORDNER
    def überordner(self):
        qs_verbindungen_üo_o = V_Ordner_Unterordner.objects.using(DB_SUPER).filter(v_unterordner = self)
        if qs_verbindungen_üo_o:
            jüngste_verbindung_üo_o = qs_verbindungen_üo_o.latest('zeitstempel')
            if jüngste_verbindung_üo_o.aktuell() and not jüngste_verbindung_üo_o.v_ordner.gelöscht():
                return jüngste_verbindung_üo_o.v_ordner
        else:
            return None

    # V_ORDNER EBENE
    def ebene(self):
        v_o = self
        ebene = 0
        while v_o.überordner():
            ebene += 1
            v_o = v_o.überordner()
        
        return ebene

    # V_ORDNER IN DB ANLEGEN
    def in_db_anlegen(self, projekt):
        # Ordner anlegen
        neuer_ordner = Ordner.objects.using(projekt.db_bezeichnung()).create(
            ist_root_ordner = self.ist_root_ordner,
            zeitstempel = timezone.now()
            )
        neuer_ordner.entlöschen(projekt)
        neuer_ordner.bezeichnung_ändern(projekt, neue_bezeichnung = self.bezeichnung())
        # Verbindung zu Vorlage
        Ordner_Vorlage.objects.using(projekt.db_bezeichnung()).create(
            ordner = neuer_ordner,
            v_ordner_id = self.id,
            )
        # Freigaben übernehmen
        neuer_ordner.freigaben_von_vorlage_übernehmen(projekt)

    def instanz(self, projekt):
        return Ordner_Vorlage.objects.using(projekt.db_bezeichnung()).get(v_ordner_id = self.id).ordner

    def ordnerbaum_in_db_anlegen(self, projekt):
        def rekursion_ordnerbaum_anlegen(v_ordner):
        # Legt Ordnerbaum unterhalb von v_ordner in Ziel-DB an
            for v_uo in v_ordner.liste_unterordner():
                # Ordner anlegen
                v_uo.in_db_anlegen(projekt)
                # Verbindung anlegen
                verbindung_o_uo = Ordner_Unterordner.objects.using(projekt.db_bezeichnung()).create(
                    ordner = Ordner.objects.using(projekt.db_bezeichnung()).get(ordner_vorlage__v_ordner_id = v_ordner.id),
                    unterordner = Ordner.objects.using(projekt.db_bezeichnung()).get(ordner_vorlage__v_ordner_id = v_uo.id),
                    zeitstempel = timezone.now()
                    )
                verbindung_o_uo.aktualisieren(projekt)
                rekursion_ordnerbaum_anlegen(v_uo)
        
        # Zuerst Ordner in DB anlegen, dann unterliegenden Ordnerbaum durch Rekursion anlegen
        self.in_db_anlegen(projekt)
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
    def aktualisieren(self):
        V_Ordner_Unterordner_Aktuell.objects.using(DB_SUPER).create(
            v_ordner_unterordner = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualiseren(self):
        V_Ordner_Unterordner_Aktuell.objects.using(DB_SUPER).create(
            v_ordner_unterordner = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_Ordner_Unterordner_Aktuell.objects.using(DB_SUPER).filter(v_ordner_unterordner = self).latest('zeitstempel').aktuell

    # V_ORDNER-UNTERORDNER IN DB ANLEGEN
    def in_db_anlegen(self, projekt):
        Ordner_Unterordner.objects.using(projekt.db_bezeichnung()).create(
            ordner = Ordner.objects.using(projekt.db_bezeichnung()).get(ordner_vorlage__v_ordner_id = self.v_ordner.id),
            unterordner = Ordner.objects.using(projekt.db_bezeichnung()).get(ordner_vorlage__v_ordner_id = self.v_unterordner.id),
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
    def bezeichnung_ändern(self, neue_bezeichnung):
        V_Rolle_Bezeichnung.objects.using(DB_SUPER).create(
            v_rolle = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self):
        return V_Rolle_Bezeichnung.objects.using(DB_SUPER).filter(v_rolle = self).latest('zeitstempel').bezeichnung

    # V_ROLLE LÖSCHEN
    def löschen(self):
        V_Rolle_Gelöscht.objects.using(DB_SUPER).create(
            v_rolle = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        return V_Rolle_Gelöscht.objects.using(DB_SUPER).filter(v_rolle = self).latest('zeitstempel').gelöscht

    # V_ROLLE IN DB ANLEGEN
    def in_db_anlegen(self, projekt):
        # Rolle anlegen
        neue_rolle = Rolle.objects.using(projekt.db_bezeichnung()).create(
            zeitstempel = timezone.now()
            )
        neue_rolle.bezeichnung_ändern(projekt, neue_bezeichnung = self.bezeichnung())
        neue_rolle.entlöschen(projekt)
        # Verbindung zu Vorlage
        Rolle_Vorlage.objects.using(projekt.db_bezeichnung()).create(
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

    def aktualisieren(self):
        V_Ordner_Rolle_Aktuell.objects.using(DB_SUPER).create(
            v_ordner_rolle = self,
            aktuell = True, 
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_Ordner_Rolle_Aktuell.objects.using(DB_SUPER).filter(v_ordner_rolle = self).latest('zeitstempel').aktuell

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
    def bezeichnung_ändern(self, neue_bezeichnung):
        V_WFSch_Bezeichnung.objects.using(DB_SUPER).create(
            v_wfsch = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self):
        return V_WFSch_Bezeichnung.objects.using(DB_SUPER).filter(v_wfsch = self).latest('zeitstempel').bezeichnung

    # V_WORKFLOW_SCHEMA GELÖSCHT
    def löschen(self):
        V_WFSch_Gelöscht.object.using(DB_SUPER).create(
            v_wfsch = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self):
        V_WFSch_Gelöscht.object.using(DB_SUPER).create(
            v_wfsch = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        return V_WFSch_Gelöscht.objects.using(DB_SUPER).filter(v_wfsch = self).latest('zeitstempel').gelöscht

    # V_WORKFLOW_SCHEMA ANFANGSSTUFE
    def anfangsstufe_festlegen(self, v_anfangsstufe):
        V_WFSch_Anfangsstufe.objects.using(DB_SUPER).create(
            v_wfsch = self,
            v_anfangsstufe = v_anfangsstufe,
            zeitstempel = timezone.now()
            )
    
    def anfangsstufe(self):
        return V_WFSch_Anfangsstufe.objects.using(DB_SUPER).filter(v_wfsch = self).latest('zeitstempel').v_anfangsstufe
            
    # V_WORKFLOW_SCHEMA IN DB ANLEGEN
    def in_db_anlegen(self, projekt):
        # Nur anlegen wenn nicht bereits Instanz vorhanden
        if not self.instanz(projekt):
        
            neues_wfsch = Workflow_Schema.objects.using(projekt.db_bezeichnung()).create(
                zeitstempel = timezone.now(),
            )
            neues_wfsch.bezeichnung_ändern(projekt, neue_bezeichnung = self.bezeichnung())
            neues_wfsch.entlöschen(projekt)
            verbindung_vorlage = WFSch_Vorlage.objects.using(projekt.db_bezeichnung()).create(
                wfsch = neues_wfsch,
                v_wfsch_id = self.id,
                zeitstempel = timezone.now()
                )

            # Anfangsstufe anlegen
            instanz_anfangsstufe = self.anfangsstufe().in_db_anlegen(projekt)
            neues_wfsch.anfangsstufe_festlegen(projekt, instanz_anfangsstufe)

            # Nachfolgende Stufen anlegen
            def rekursion_nachfolgende_stufen_anlegen(v_stufe):
                for v_s in v_stufe.liste_folgestufen():
                    # Stufe anlegen
                    neue_stufe = v_s.in_db_anlegen(projekt)
                    # Verbindung Folgestufe anlegen
                    WFSch_Stufe_Folgestufe.objects.using(projekt.db_bezeichnung()).create(
                        wfsch_stufe = v_stufe.instanz(projekt),
                        wfsch_folgestufe = neue_stufe,
                        zeitstempel = timezone.now()
                        )
                    rekursion_nachfolgende_stufen_anlegen(v_s)

            rekursion_nachfolgende_stufen_anlegen(self.anfangsstufe())

    def instanz(self, projekt):
        verbindungen_zu_instanzen = WFSch_Vorlage.objects.using(projekt.db_bezeichnung()).filter(v_wfsch_id = self.id)
        if verbindungen_zu_instanzen and not verbindungen_zu_instanzen.latest('zeitstempel').wfsch.gelöscht(projekt):
            jüngste_instanz = verbindungen_zu_instanzen.latest('zeitstempel').wfsch
            if not jüngste_instanz.gelöscht(projekt):
                return jüngste_instanz
        # Wenn keine Instanz vorhanden: None zurückgeben
        return None

    # V_WORKFLOW_SCHEMA DICT
    def v_wfsch_dict(self):
        wfsch_d = self.__dict__
        wfsch_d['bezeichnung'] = self.bezeichnung()

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
    def bezeichnung_ändern(self, neue_bezeichnung):
        V_WFSch_Stufe_Bezeichnung.objects.using(DB_SUPER).create(
            v_wfsch_stufe = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self):
        return V_WFSch_Stufe_Bezeichnung.objects.using(DB_SUPER).filter(v_wfsch_stufe = self).latest('zeitstempel').bezeichnung

    # V_WFSCH_STUFE GELÖSCHT
    def löschen(self):
        V_WFSch_Stufe_Gelöscht.objects.using(DB_SUPER).create(
            v_wfsch_stufe = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self):
        V_WFSch_Stufe_Gelöscht.objects.using(DB_SUPER).create(
            v_wfsch_stufe = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        return V_WFSch_Stufe_Gelöscht.objects.using(DB_SUPER).filter(v_wfsch_stufe = self).latest('zeitstempel').gelöscht

    # V_WFSCH_STUFE LISTE FOLGESTUFEN
    def liste_folgestufen(self):
        li_folgestufen = []
        for verbindung_v_fs in V_WFSch_Stufe_Folgestufe.objects.using(DB_SUPER).filter(v_wfsch_stufe = self):
            if verbindung_v_fs.aktuell() and not verbindung_v_fs.v_wfsch_folgestufe.gelöscht():
                li_folgestufen.append(verbindung_v_fs.v_wfsch_folgestufe)
        return li_folgestufen

    # V_WFSCH_STUFE LISTE ROLLEN
    def liste_rollen(self):
        li_rollen = []
        for verbindung_s_r in V_WFSch_Stufe_Rolle.objects.using(DB_SUPER).filter(v_wfsch_stufe = self):
            if verbindung_s_r.aktuell() and not verbindung_s_r.v_rolle.gelöscht():
                li_rollen.append(verbindung_s_r.v_rolle)
        return li_rollen

    # V_WFSCH_STUFE IN DB ANLEGEN
    def in_db_anlegen(self, projekt):
    # Wird nur für anlegen von WFSCH gebraucht --> Verbindung zu Folgestufen erfolg in Funktion für Anlegn WFSch
        # Stufe anlegen
        neue_wfsch_stufe = WFSch_Stufe.objects.using(projekt.db_bezeichnung()).create(
            zeitstempel = timezone.now()
            )
        neue_wfsch_stufe.bezeichnung_ändern(projekt, neue_bezeichnung = self.bezeichnung())
        neue_wfsch_stufe.entlöschen(projekt)
        # Verbdindung zu Vorlage anlegen
        WFSch_Stufe_Vorlage.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe = neue_wfsch_stufe,
            v_wfsch_stufe_id = self.id,
            zeitstempel = timezone.now()
            )
        # Verbindungen zu Rollen anlegen
        for v_r in self.liste_rollen():
            # Rolle anlegen wenn nötig
            try:
                rolle = Rolle_Vorlage.objects.using(projekt.db_bezeichnung()).get(v_rolle_id = v_r.id).rolle
            except ObjectDoesNotExist:
                rolle = v_r.in_db_anlegen(projekt)
            # Verbindung zu Rolle anlegen
            verbindung_stufe_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).create(
                wfsch_stufe = neue_wfsch_stufe,
                rolle = rolle,
                zeitstempel = timezone.now()
                )
            verbindung_stufe_rolle.aktualisieren(projekt)
        
        # Stufe zurückgeben
        return neue_wfsch_stufe

    def instanz(self, projekt):
        verbindungen_zu_instanzen = WFSch_Stufe_Vorlage.objects.using(projekt.db_bezeichnung()).filter(v_wfsch_stufe_id = self.id)
        if verbindungen_zu_instanzen:
            jüngste_instanz = verbindungen_zu_instanzen.latest('zeitstempel').wfsch_stufe
            if not jüngste_instanz.gelöscht(projekt):
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

    def aktualisieren(self):
        V_WFSch_Stufe_Folgestufe.objects.using(DB_SUPER).create(
            v_wfsch_stufe_folgestufe = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        V_WFSch_Stufe_Folgestufe.objects.using(DB_SUPER).create(
            v_wfsch_stufe_folgestufe = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_WFSch_Stufe_Folgestufe_Aktuell.objects.using(DB_SUPER).filter(v_wfsch_stufe_folgestufe = self).latest('zeitstempel').aktuell

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
    def aktualisieren(self):
        V_Ordner_WFSch_Aktuell.objects.using(DB_SUPER).create(
            v_ordner_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        V_Ordner_WFSch_Aktuell.objects.using(DB_SUPER).create(
            v_ordner_wfsch = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_Ordner_WFSch_Aktuell.objects.using(DB_SUPER).filter(v_ordner_wfsch = self).latest('zeitstempel').aktuell

class V_Ordner_WFSch_Aktuell(models.Model):
    v_ordner_wfsch = models.ForeignKey(V_Ordner_WFSch, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_WFSch_Stufe_Rolle(models.Model):
    v_wfsch_stufe = models.ForeignKey(V_WFSch_Stufe, on_delete = models.CASCADE)
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self):
        V_WFSch_Stufe_Rolle_Aktuell.objects.using(DB_SUPER).create(
            v_wfsch_stufe_rolle = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self):
        V_WFSch_Stufe_Rolle_Aktuell.objects.using(DB_SUPER).create(
            v_wfsch_stufe_rolle = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_WFSch_Stufe_Rolle_Aktuell.objects.using(DB_SUPER).filter(v_wfsch_stufe_rolle = self).latest('zeitstempel').aktuell

class V_WFSch_Stufe_Rolle_Aktuell(models.Model):
    v_wfsch_stufe_rolle = models.ForeignKey(V_WFSch_Stufe_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Projektstruktur(models.Model):
    zeitstempel = models.DateTimeField()

    # V_PJS GELÖSCHT
    def löschen(self):
        V_PJS_Gelöscht.objects.using(DB_SUPER).create(
            v_pjs = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )

    def entlöschen(self):
        V_PJS_Gelöscht.objects.using(DB_SUPER).create(
            v_pjs = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        return V_PJS_Gelöscht.objects.using(DB_SUPER).filter(v_pjs = self).latest('zeitstempel').gelöscht

    # V_PJS BEZEICHNUNG
    def bezeichnung_ändern(self, bezeichnung):
        V_PJS_Bezeichnung.objects.using(DB_SUPER).create(
            v_pjs = self,
            bezeichnung = bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self):
        return V_PJS_Bezeichnung.objects.using(DB_SUPER).filter(v_pjs = self).latest('zeitstempel').bezeichnung

    # V_PJS ORDNER
    def ordner_hinzufügen(self, v_ordner):
        # Verbindung anlegen, wenn noch nicht vorhanden
        verbindung_zu_ordner = V_PJS_Ordner.objects.using(DB_SUPER).get_or_create(
            v_pjs = self,
            v_ordner = v_ordner,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_zu_ordner.aktualisieren()

    def ordner_entfernen(self, v_ordner):
        verbindung_zu_ordner = V_PJS_Ordner.objects.using(DB_SUPER).get(
            v_pjs = self,
            v_ordner = v_ordner)
        verbindung_zu_ordner.entaktualisieren()

    def liste_ordner(self):
        li_ordner= []
        for v in V_PJS_Ordner.objects.using(DB_SUPER).filter(v_pjs = self):
            if v.aktuell() and not v.v_ordner.gelöscht():
                li_ordner.append(v.v_ordner)
        return li_ordner

    def liste_verbindungen_ordner_wfsch(self):
        li_verbindungen_o_wfsch = []
        for v_o in self.liste_ordner():
            try:
                verbindung_o_wfsch = V_Ordner_WFSch.objects.using(DB_SUPER).filter(v_ordner = v_o).latest('zeitstempel')
                li_verbindungen_o_wfsch.append(verbindung_o_wfsch)
            except ObjectDoesNotExist:
                pass
        return li_verbindungen_o_wfsch

    def root_v_ordner(self):
        for v_pjs_o in V_PJS_Ordner.objects.using(DB_SUPER).filter(v_pjs = self):
            if v_pjs_o.aktuell():
                v_o = v_pjs_o.v_ordner
                if v_o.ist_root_ordner and not v_o.gelöscht():
                    return v_o

    def ordnerstruktur_in_db_anlegen(self, projekt):
        for oberster_v_o in liste_oberste_v_ordner():
            oberster_v_o.ordnerbaum_in_db_anlegen(projekt)

    # V_PJS WFSCH
    def wfsch_hinzufügen(self, v_wfsch):
        # Verbindung anlegen, wenn noch nicht vorhanden
        verbindung_zu_wfsch = V_PJS_WFSch.objects.using(DB_SUPER).get_or_create(
            v_pjs = self,
            v_wfsch = v_wfsch,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_zu_wfsch.aktualisieren()

    def wfsch_entfernen(self, v_wfsch):
        verbindung_zu_wfsch = V_PJS_WFSch.objects.using(DB_SUPER).get(
            v_pjs = self,
            v_wfsch = v_wfsch
            )
        verbindung_zu_wfsch.entaktualisieren()

    def liste_wfsch(self):
        li_wfsch = []
        for verbindung_pjs_wfsch in V_PJS_WFSch.objects.using(DB_SUPER).filter(v_pjs = self):
            if verbindung_pjs_wfsch.aktuell() and not verbindung_pjs_wfsch.v_wfsch.gelöscht():
                li_wfsch.append(verbindung_pjs_wfsch.v_wfsch)
        return li_wfsch

    def workflowschemata_in_db_anlegen(self, projekt):
        for wfsch in self.liste_wfsch():
            wfsch.in_db_anlegen(projekt)

    # V_PJS ROLLEN
    def rolle_hinzufügen(self, v_rolle):
        verbindung_zu_rolle = V_PJS_Rolle.objects.using(DB_SUPER).get_or_create(
            v_pjs = self,
            v_rolle = v_rolle, 
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_zu_rolle.aktivieren()

    def rolle_entfernen(self, v_rolle):
        verbindung_zu_rolle = V_PJS_Rolle.objects.using(DB_SUPER).get(
            v_pjs = self,
            v_rolle = v_rolle,
            )
        verbindung_zu_rolle.entaktualisieren()

    # V_PJS DICT
    def v_pjs_dict(self):
        dict_pjs = self.__dict__
        dict_pjs['bezeichnung'] = self.bezeichnung()

        return dict_pjs

    # V_PJS AUF PROJEKT ÜBERTRAGEN
    def in_db_anlegen(self, projekt):
        Projektstruktur.objects.using(projekt.db_bezeichnung()).create(
            v_pjs_id = self.id,
            zeitstempel = timezone.now()
            )
        self.ordnerstruktur_in_db_anlegen(projekt)
        self.workflowschemata_in_db_anlegen(projekt)
        
        # Verbindungen Ordner-WFSch anlegen
        for verbindung_o_wfsch in self.liste_verbindungen_ordner_wfsch():
            instanz_verbindung_o_wfsch = Ordner_WFSch.objects.using(projekt.db_bezeichnung()).create(
                ordner = verbindung_o_wfsch.v_ordner.instanz(projekt),
                wfsch = verbindung_o_wfsch.v_wfsch.instanz(projekt),
                zeitstempel = timezone.now()
                )
            instanz_verbindung_o_wfsch.aktualisieren(projekt)

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

    def aktualisieren(self):
        V_PJS_Ordner_Aktuell.objects.using(DB_SUPER).create(
            v_pjs_ordner = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        V_PJS_Ordner_Aktuell.objects.using(DB_SUPER).create(
            v_pjs_ordner = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_PJS_Ordner_Aktuell.objects.using(DB_SUPER).filter(v_pjs_ordner = self).latest('zeitstempel').aktuell

class V_PJS_Ordner_Aktuell(models.Model):
    v_pjs_ordner = models.ForeignKey(V_PJS_Ordner, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_PJS_WFSch(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    v_wfsch = models.ForeignKey(V_Workflow_Schema, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    def aktualisieren(self):
        V_PJS_WFSch_Aktuell.objects.using(DB_SUPER).create(
            v_pjs_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        V_PJS_WFSch_Aktuell.objects.using(DB_SUPER).create(
            v_pjs_wfsch = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_PJS_WFSch_Aktuell.objects.using(DB_SUPER).filter(v_pjs_wfsch = self).latest('zeitstempel').aktuell

class V_PJS_WFSch_Aktuell(models.Model):
    v_pjs_wfsch = models.ForeignKey(V_PJS_WFSch, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_PJS_Rolle(models.Model):
    v_pjs = models.ForeignKey(V_Projektstruktur, on_delete = models.CASCADE)
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    v_zeitstempel = models.DateTimeField()

    def aktualisieren(self):
        V_PJS_Rolle_Aktuell.objects.using(DB_SUPER).create(
            v_pjs_rolle = self,
            aktiv = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        V_PJS_Rolle_Aktuell.objects.using(DB_SUPER).create(
            v_pjs_rolle = self,
            aktiv = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return V_PJS_Rolle_Aktuell.objects.using(DB_SUPER).filter(v_pjs_rolle = self).latest('zeitstempel').aktiv

class V_PJS_Rolle_Aktuell(models.Model):
    v_pjs_rolle = models.ForeignKey(V_PJS_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

# ROLLE

class Rolle(models.Model):
    zeitstempel = models.DateTimeField()

    # ROLLE BEZEICHNUNG
    def bezeichnung_ändern(self, projekt, neue_bezeichnung):
        Rolle_Bezeichnung.objects.using(projekt.db_bezeichnung()).create(
            rolle = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, projekt):
        return Rolle_Bezeichnung.objects.using(projekt.db_bezeichnung()).filter(rolle = self).latest('zeitstempel').bezeichnung

    # ROLLE LÖSCHEN
    def löschen(self, projekt):
        Rolle_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            rolle = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, projekt):
        Rolle_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            rolle = self, 
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, projekt):
        return Rolle_Gelöscht.objects.using(projekt.db_bezeichnung()).filter(rolle = self).latest('zeitstempel').gelöscht

    # ROLLE FIRMA
    def firma_zuweisen(self, projekt, firma):
        neue_verbindung_r_f = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
            rolle = self,
            firma_id = firma.id, 
            defaults = {'zeitstempel':timezone.now()}
            )[0]
        if not neue_verbindung_r_f.aktuell(projekt):
            neue_verbindung_r_f.aktualisieren(projekt)

    def ist_firmenrolle(self, projekt, firma):
        # Prüfen ob Verbindung Rolle-Firma aktuell
        try:
            verbindung_r_fa = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get(rolle = self, firma_id = firma.id)
            if verbindung_r_fa.aktuell(projekt):
                return True
            else:
                return False
        # Wenn keine Vebindung Rolle-Firam: False zurückgeben
        except ObjectDoesNotExist:
            return False

    def ist_firmenrolle_ändern(self, projekt, firma, ist_firmenrolle):
        verbindung_r_fa = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
            rolle = self,
            firma_id = firma.id,
            defaults = {'zeitstempel':timezone.now()}
            )[0]

        if ist_firmenrolle == True:
            verbindung_r_fa.aktualisieren(projekt)
        else:
            verbindung_r_fa.entaktualisieren(projekt)

    # ROLLE MITARBEITER
    def verbindung_rolle_mitarbeiter(self, projekt, mitarbeiter):
        try:
            verbindung_rolle_firma = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get(rolle = self, firma_id = mitarbeiter.firma.id)
            verbindung_rolle_mitarbeiter = Rolle_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get(
                rolle_firma = verbindung_rolle_firma, 
                mitarbeiter_id = mitarbeiter.id
                )
            return verbindung_rolle_mitarbeiter
        except ObjectDoesNotExist:
            return None

    def ist_mitarbeiterrolle(self, projekt, mitarbeiter):
        # Prüfen ob Verbindung Rolle-Mitarbeiter aktuell
        try:
            verbindung_ro_fa = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get(rolle = self, firma_id = mitarbeiter.firma.id)
            verbindung_ro_ma = Rolle_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get(rolle_firma = verbindung_ro_fa, mitarbeiter_id = mitarbeiter.id)
            if verbindung_ro_ma.aktuell(projekt):
                return True
            else:
                return False
        except ObjectDoesNotExist:
            return False

    def rolleninhaber_hinzufügen(self, projekt, mitarbeiter):
        verbindung_rolle_firma = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get(rolle = self, firma_id = mitarbeiter.firma.id)
        verbindung_rolle_mitarbeiter = Rolle_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get_or_create(
            rolle_firma = verbindung_rolle_firma,
            mitarbeiter_id = mitarbeiter.id,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_rolle_mitarbeiter.aktualisieren(projekt)

    def rolleninhaber_lösen(self, projekt, mitarbeiter):
        verbindung_rolle_firma = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get(rolle = self, firma_id = mitarbeiter.firma.id)
        verbindung_rolle_mitarbeiter = Rolle_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get(
            rolle_firma = verbindung_rolle_firma,
            mitarbeiter_id = mitarbeiter.id,
            )
        verbindung_rolle_mitarbeiter.entaktualisieren(projekt)

    def mitarbeiter_ist_rolleninhaber(self, projekt, mitarbeiter):
        verbindung_rolle_mitarbeiter = self.verbindung_rolle_mitarbeiter(projekt, mitarbeiter)
        if verbindung_rolle_mitarbeiter:
            return verbindung_rolle_mitarbeiter.aktuell(projekt)
        else:
            return None

    def liste_rolleninhaber_firma(self, projekt, firma):
        db_projekt = projekt.db_bezeichnung()
        verbindung_ro_fa = Rolle_Firma.objects.using(db_projekt).get(rolle = self, firma_id = firma.id)
        qs_verbindungen_ro_ma = Rolle_Mitarbeiter.objects.using(db_projekt).filter(rolle_firma = verbindung_ro_fa)
        li_rolleninhaber_firma = []
        User = get_user_model()
        for verbindung_ro_ma in qs_verbindungen_ro_ma:
            if verbindung_ro_ma.aktuell(projekt):
                ma = User.objects.using(DB_SUPER).get(pk = verbindung_ro_ma.mitarbeiter_id)
                if not ma.gelöscht():
                    li_rolleninhaber_firma.append(ma)
        return li_rolleninhaber_firma

    def liste_rolleninhaber_firma_dict(self, projekt, firma):
        li_ri_dict = []
        for ri in self.liste_rolleninhaber_firma(projekt, firma):
            li_ri_dict.append(ri.mitarbeiter_dict())
        return li_ri_dict

    def liste_nicht_rolleninhaber_firma(self, projekt, firma):
        li_nicht_rolleninhaber = []
        li_rolleninhaber = self.liste_rolleninhaber_firma(projekt, firma)
        for ma in firma.liste_mitarbeiter():
            if ma not in li_rolleninhaber:
                li_nicht_rolleninhaber.append(ma)
        return li_nicht_rolleninhaber

    def liste_nicht_rolleninhaber_firma_dict(self, projekt, firma):
        li_nri_dict = []
        for nri in self.liste_nicht_rolleninhaber_firma(projekt, firma):
            li_nri_dict.append(nri.mitarbeiter_dict())
        return li_nri_dict

    # ROLLE DICT
    def dict_rolle(self, projekt):
        rolle_d = self.__dict__
        rolle_d['bezeichnung'] = self.bezeichnung(projekt)

        return rolle_d

    # ROLLE FREIGABEN AUF FIRMA ÜBERTRAGEN
    def freigaben_übertragen_firma(self, projekt, firma):
        for o in liste_ordner(projekt):
            if o.lesefreigabe_rolle(projekt, self) and not o.lesefreigabe_firma(projekt, firma):
                o.lesefreigabe_erteilen_firma(projekt, firma)
            if o.uploadfreigabe_rolle(projekt, self) and not o.uploadfreigabe_firma(projekt, firma):
                o.uploadfreigabe_erteilen_firma(projekt, firma)

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
    def aktualisieren(self, projekt):
        Rolle_Firma_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            rolle_firma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, projekt):
        Rolle_Firma_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            rolle_firma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        return Rolle_Firma_Aktuell.objects.using(projekt.db_bezeichnung()).filter(rolle_firma = self).latest('zeitstempel').aktuell

class Rolle_Firma_Aktuell(models.Model):
    rolle_firma = models.ForeignKey(Rolle_Firma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Rolle_Mitarbeiter(models.Model):
    rolle_firma = models.ForeignKey(Rolle_Firma, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    mitarbeiter_id = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

    # ROLLE_MITARBEITER AKTUELL
    def aktualisieren(self, projekt):
        Rolle_Mitarbeiter_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            rolle_mitarbeiter = self,
            aktuell = True, 
            zeitstempel = timezone.now() 
            )
    
    def entaktualisieren(self, projekt):
        Rolle_Mitarbeiter_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            rolle_mitarbeiter = self,
            aktuell = False, 
            zeitstempel = timezone.now() 
            )

    def aktuell(self, projekt):
        try:
            return Rolle_Mitarbeiter_Aktuell.objects.using(projekt.db_bezeichnung()).filter(rolle_mitarbeiter = self).latest('zeitstempel').aktuell
        except ObjectDoesNotExist:
            return False

class Rolle_Mitarbeiter_Aktuell(models.Model):
    rolle_mitarbeiter = models.ForeignKey(Rolle_Mitarbeiter, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Rolle_Vorlage(models.Model):
    rolle = models.ForeignKey(Rolle, on_delete = models.CASCADE)
    v_rolle_id = models.CharField(max_length = 20)
    # Es soll nur eine Verbindung zur Vorlage geben --> Zeitstempel kann von Rolle übernommen werden

# WFSCH

class Workflow_Schema(models.Model):
    # bezeichnung = models.CharField(max_length = 50, null = True) # TODO: Feld Löschen
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # WORKFLOW_SCHEMA BEZEICHNUNG
    def bezeichnung_ändern(self, projekt, neue_bezeichnung):
        WFSch_Bezeichnung.objects.using(projekt.db_bezeichnung()).create(
            wfsch = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def _bezeichnung(self, projekt):
        return WFSch_Bezeichnung.objects.using(projekt.db_bezeichnung()).filter(wfsch = self).latest('zeitstempel').bezeichnung

    # WORKFLOW_SCHEMA GELÖSCHT
    def löschen(self, projekt):
        WFSch_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            wfsch = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )
        
        # Stufen löschen
        stufe = self.anfangsstufe(projekt)
        while stufe:
            stufe.löschen(projekt)
            stufe = stufe.folgestufe(projekt)
            
    def entlöschen(self, projekt):
        WFSch_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            wfsch = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )
        
    def gelöscht(self, projekt):
        return WFSch_Gelöscht.objects.using(projekt.db_bezeichnung()).filter(wfsch = self).latest('zeitstempel').gelöscht

    # WORKFLOW_SCHEMA ANFANGSSTUFE
    def anfangsstufe_festlegen(self, projekt, anfangsstufe):
        WFSch_Anfangsstufe.objects.using(projekt.db_bezeichnung()).create(
            wfsch = self,
            anfangsstufe = anfangsstufe,
            zeitstempel = timezone.now()
            )
    
    def anfangsstufe(self, projekt):
        return WFSch_Anfangsstufe.objects.using(projekt.db_bezeichnung()).filter(wfsch = self).latest('zeitstempel').anfangsstufe

    def letzte_stufe(self, projekt):
        # Letzte Stufe ist die Stufe ohne Folgestufe
        for s in self.liste_stufen(projekt):
            if not s.folgestufe(projekt):
                return s

    # WORKFLOW_SCHEMA STUFEN
    def stufe_hinzufügen(self, projekt, bezeichnung_stufe):
        # Neue Stufe anlegen
        neue_wfsch_stufe = WFSch_Stufe.objects.using(projekt.db_bezeichnung()).create(
            zeitstempel = timezone.now()
            )
        neue_wfsch_stufe.entlöschen(projekt)
        neue_wfsch_stufe.bezeichnung_ändern(projekt, neue_bezeichnung = bezeichnung_stufe)
        # Neue Stufe wird Folgestufe von bisheriger letzter Stufe
        self.letzte_stufe(projekt).folgestufe_festlegen(projekt, neue_wfsch_stufe)

    def liste_stufen(self, projekt):
        stufe = self.anfangsstufe(projekt)
        li_stufen = []
        while stufe:
            li_stufen.append(stufe)
            stufe = stufe.folgestufe(projekt)
        return li_stufen
    
    def liste_stufen_dict(self, projekt, firma = None):
        li_stufen_dict = []
        for s in self.liste_stufen(projekt):
            li_stufen_dict.append(s.wfsch_stufe_dict(projekt, firma))
        return li_stufen_dict

    # WORKFLOW_SCHEMA PRÜFER
    def firmenprüfer_nach_rollen_zuweisen(self, projekt, firma):
        for s in self.liste_stufen(projekt):
            if s._firma_ist_prüffirma(projekt, firma):
                for ro in s._liste_rollen(projekt):
                    if ro.ist_firmenrolle(projekt, firma):
                        for ma in firma.liste_mitarbeiter():
                            if ro.ist_mitarbeiterrolle(projekt, ma):
                                wfschSt_ro = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe = s, rolle = ro)
                                wfschSt_fa = WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe_rolle = wfschSt_ro, firma_id = firma.id)
                                wfschSt_fa.firmenprüfer_hinzufügen(projekt, ma)

    # WORKFLOW_SCHEMA DICT
    def wfsch_dict(self, projekt, firma = None):
        wfsch_dict = self.__dict__
        wfsch_dict['bezeichnung'] = self._bezeichnung(projekt)
        wfsch_dict['liste_wfsch_stufen'] = self.liste_stufen_dict(projekt, firma)

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

# WFSCH STUFE

class WFSch_Stufe(models.Model):
    zeitstempel = models.DateTimeField()

    # WFSCH_STUFE BEZEICHNUNG
    def bezeichnung_ändern(self, projekt, neue_bezeichnung):
        WFSch_Stufe_Bezeichnung.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, projekt):
        return WFSch_Stufe_Bezeichnung.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe = self).latest('zeitstempel').bezeichnung

    # WFSCH_STUFE FOLGESTUFE
    def folgestufe_festlegen(self, projekt, folgestufe):
        WFSch_Stufe_Folgestufe.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe = self,
            wfsch_folgestufe = folgestufe,
            zeitstempel = timezone.now()
            )
    
    def folgestufe(self, projekt):
        qs_verbindungen_s_fs = WFSch_Stufe_Folgestufe.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe = self)
        # Wenn keine Folgestufe: None zurückgeben
        if qs_verbindungen_s_fs:
            fs = qs_verbindungen_s_fs.latest('zeitstempel').wfsch_folgestufe
            if not fs.gelöscht(projekt):
                return qs_verbindungen_s_fs.latest('zeitstempel').wfsch_folgestufe
            else:
                return None
        else:
            return None

    # WFSCH_STUFE LÖSCHEN
    def löschen(self, projekt):
        WFSch_Stufe_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, projekt):
        WFSch_Stufe_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, projekt):
        return WFSch_Stufe_Gelöscht.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe = self).latest('zeitstempel').gelöscht

    # WFSCH_STUFE ROLLEN
    def rolle_hinzufügen(self, projekt, rolle):
        verbindung_wfsch_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe = self,
            rolle = rolle,
            zeitstempel = timezone.now()
            )
        verbindung_wfsch_rolle.aktualisieren(projekt)

    def rolle_lösen(self, projekt, rolle):
        verbindung_wfsch_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).get(
            wfsch_stufe = self,
            rolle = rolle
            )
        verbindung_wfsch_rolle.entaktualisieren(projekt)

    def _liste_rollen(self, projekt):
        li_rollen = []
        for verbindung_wfschSt_r in WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe = self):
            if verbindung_wfschSt_r.aktuell(projekt) and not verbindung_wfschSt_r.rolle.gelöscht(projekt):
                li_rollen.append(verbindung_wfschSt_r.rolle)
        return li_rollen

    def liste_rollen_dict(self, projekt, firma = None):
        li_rollen_dict= []
        for r in self._liste_rollen(projekt):
            rolle_dict = r.__dict__
            rolle_dict['bezeichnung'] = r.bezeichnung(projekt)
            verbindung_wfsch_stufe_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe = self, rolle = r)
            rolle_dict['liste_prüffirmen'] = verbindung_wfsch_stufe_rolle.liste_firmen_dict(projekt)
            
            if firma:
                rolle_dict['rolle_ist_firmenrolle'] = True if firma in verbindung_wfsch_stufe_rolle.liste_firmen(projekt) else False

            li_rollen_dict.append(rolle_dict)
        return li_rollen_dict

    # WFSCH_STUFE FIRMEN
    def prüffirma_hinzufügen(self, projekt, rolle, firma):
        verbindung_wfschSt_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe = self, rolle = rolle)
        verbindung_wfschSt_firma = WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
            wfsch_stufe_rolle = verbindung_wfschSt_rolle, 
            firma_id = firma.id,
            defaults = {'zeitstempel':timezone.now()}
            )[0]
        if not verbindung_wfschSt_firma.aktuell(projekt): 
            verbindung_wfschSt_firma.aktualisieren(projekt)

    def prüffirma_lösen(self, projekt, rolle, firma_id):
        verbindung_wfschSt_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe = self, rolle = rolle)
        verbindung_wfschSt_firma = WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).get(
            wfsch_stufe_rolle = verbindung_wfschSt_rolle,
            firma_id = firma_id
            )
        verbindung_wfschSt_firma.entaktualisieren(projekt)

    def liste_prüffirmen(self, projekt):
        li_prüffirmen = []
        for r in self._liste_rollen(projekt):
            verbindung_wfschSt_rolle = WFSch_Stufe_Rolle.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe = self, rolle = r)
            for fa in verbindung_wfschSt_rolle.liste_firmen(projekt):
                if not fa in li_prüffirmen:
                    li_prüffirmen.append(fa)
        return li_prüffirmen

    def liste_nicht_prüffirmen(self, projekt):
        li_nicht_prüffirmen = []
        for fa in projekt.liste_projektfirmen():
            if fa not in self.liste_prüffirmen(projekt):
                li_nicht_prüffirmen.append(fa)
        return li_nicht_prüffirmen 

    def liste_nicht_prüffirmen_dict(self, projekt):
        li_nicht_pf_dict = []
        for pf in self.liste_nicht_prüffirmen(projekt):
            li_nicht_pf_dict.append(pf.firma_dict())
        return li_nicht_pf_dict

    def _firma_ist_prüffirma(self, projekt, firma):
        if firma in self.liste_prüffirmen(projekt):
            return True
        else:
            return False

    # WFSCH_STUFE DICT

    def wfsch_stufe_dict(self, projekt, firma):
        wfsch_s_dict = self.__dict__
        wfsch_s_dict['liste_nicht_prüffirmen'] = self.liste_nicht_prüffirmen_dict(projekt)
        wfsch_s_dict['liste_rollen'] = self.liste_rollen_dict(projekt, firma)
        wfsch_s_dict['bezeichnung'] = self.bezeichnung(projekt)
        
        if firma:
            wfsch_s_dict['firma_ist_prüffirma'] = self._firma_ist_prüffirma(projekt, firma)

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
    def aktualisieren(self, projekt):
        WFSch_Stufe_Rolle_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_rolle = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self, projekt):
        WFSch_Stufe_Rolle_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_rolle = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        return WFSch_Stufe_Rolle_Aktuell.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe_rolle = self).latest('zeitstempel').aktuell

    # WFSCH_STUFE_ROLLE FIRMEN
    def firma_hinzufügen(self, projekt, firma_id):
        verbindung_firma = WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
            wfsch_stufe_rolle = self,
            firma_id = firma_id,
            zeitstempel = timezone.now()
            )[0]
        verbindung_firma.aktualisieren(projekt)

    def firma_lösen(self, projekt, firma_id):
        verbindung_firma = WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).get(
            wfsch_stufe_rolle = self,
            firma_id = firma_id,
            zeitstempel = timezone.now()
            )
        verbindung_firma.entaktualisieren(projekt)

    def liste_firmen(self, projekt):
        li_firmen = []
        for verbindung_firma in WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe_rolle = self):
            firma = Firma.objects.using(DB_SUPER).get(pk = verbindung_firma.firma_id)
            if verbindung_firma.aktuell(projekt) and not firma.gelöscht():
                li_firmen.append(firma)
        return li_firmen
    
    def liste_firmen_dict(self, projekt):
        li_firmen_dict = []
        for fa in self.liste_firmen(projekt):
            dict_fa = fa.firma_dict()
            verbindung_wfschSt_fa = WFSch_Stufe_Firma.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe_rolle = self, firma_id = fa.id)
            dict_fa['liste_firmenprüfer'] = verbindung_wfschSt_fa._liste_firmenprüfer(projekt)
            dict_fa['liste_nicht_firmenprüfer'] = verbindung_wfschSt_fa._liste_nicht_firmenprüfer(projekt)
            li_firmen_dict.append(dict_fa)
        return li_firmen_dict

    # WFSCH_STUFE_ROLLE MITARBEITER
    def liste_mitarbeiter_firma(self, projekt, firma):
        pass

class WFSch_Stufe_Rolle_Aktuell(models.Model):
    wfsch_stufe_rolle = models.ForeignKey(WFSch_Stufe_Rolle, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Firma(models.Model):
    wfsch_stufe_rolle = models.ForeignKey(WFSch_Stufe_Rolle, null = True, on_delete = models.CASCADE) # TODO: Nullable entfernen
    firma_id = models.CharField(max_length=20)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # WFSCH_STUFE_FIRMA AKTUELL
    def aktualisieren(self, projekt):
        WFSch_Stufe_Firma_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_firma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self, projekt):
        WFSch_Stufe_Firma_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_firma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        try:
            return WFSch_Stufe_Firma_Aktuell.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe_firma = self).latest('zeitstempel').aktuell
        except ObjectDoesNotExist:
            return False

    # WFSCH_STUFE_FIRMA MITARBEITER (BZW. "FIRMENPRÜFER")
    def _liste_firmenprüfer(self, projekt):
        qs_verbindungen_wfschSt_ma = WFSch_Stufe_Mitarbeiter.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe_firma = self)
        li_wfschSt_ma = []
        for verbindung_wfschSt_ma in qs_verbindungen_wfschSt_ma:
            ma = Mitarbeiter.objects.using(DB_SUPER).get(pk = verbindung_wfschSt_ma.mitarbeiter_id)
            if verbindung_wfschSt_ma.aktuell(projekt) and not ma.gelöscht():
                li_wfschSt_ma.append(ma)
        return li_wfschSt_ma

    def _liste_firmenprüfer_dict(self, projekt):
        li_wfschSt_ma_dict = []
        for ma in self._liste_firmenprüfer(projekt):
            dict_ma = ma.mitarbeiter_dict()
            verbindung_wfschSt_ma = WFSch_Stufe_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get(wfsch_stufe_firma = self)
            dict_ma['immer_erforderlich'] = verbindung_wfschSt_ma.immer_erforderlich(projekt)
            li_wfschSt_ma_dict.append(dict_ma)
        return li_wfschSt_ma_dict

    def _liste_nicht_firmenprüfer(self, projekt):
        li_nicht_fp = []
        firma = Firma.objects.using(DB_SUPER).get(pk = self.firma_id)
        for ma in firma_liste_mitarbeiter_projekt(projekt, firma):
            if not ma in self._liste_firmenprüfer(projekt):
                li_nicht_fp.append(ma)
        return li_nicht_fp

    def _liste_nicht_firmenprüfer_dict(self, projekt):
        li_nicht_fp_dict = []
        for fp in self._liste_nicht_firmenprüfer(self, projekt):
            li_nicht_fp_dict.append(fp.mitarbeiter_dict())
        return li_nicht_fp_dict

    def firmenprüfer_hinzufügen(self, projekt, firmenprüfer_neu):
        verbindung_firmenprüfer_neu = WFSch_Stufe_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get_or_create(
            wfsch_stufe_firma = self,
            mitarbeiter_id = firmenprüfer_neu.id,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_firmenprüfer_neu.aktualisieren(projekt)

    def firmenprüfer_lösen(self, projekt, firmenprüfer_lö):
        verbindung_firmenprüfer_lö = WFSch_Stufe_Mitarbeiter.objects.using(projekt.db_bezeichnung()).get(
            wfsch_stufe_firma = self,
            mitarbeiter_id = firmenprüfer_lö.id
            )
        verbindung_firmenprüfer_lö.entaktualisieren(projekt)

class WFSch_Stufe_Firma_Aktuell(models.Model):
    wfsch_stufe_firma = models.ForeignKey(WFSch_Stufe_Firma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Mitarbeiter(models.Model):
    wfsch_stufe_firma = models.ForeignKey(WFSch_Stufe_Firma, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    mitarbeiter_id = models.CharField(max_length=20, default='Das ist nicht gültig') # TODO: Default entfernen
    zeitstempel = models.DateTimeField(default = timezone.now)

    # WFSCH_STUFE_MITARBEITER AKTUELL

    def aktualisieren(self, projekt):
        WFSch_Stufe_Mitarbeiter_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_mitarbeiter = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def entaktualisieren(self, projekt):
        WFSch_Stufe_Mitarbeiter_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_mitarbeiter = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        try:
            qs_wfschSt_ma_aktuell = WFSch_Stufe_Mitarbeiter_Aktuell.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe_mitarbeiter = self)
            return qs_wfschSt_ma_aktuell.latest('zeitstempel').aktuell
        except ObjectDoesNotExist:
            return False

    # WFSCH_STUFE_MITARBEITER IMMER ERFORDERLICH
    def immer_erforderlich_ändern(self, projekt, immer_erforderlich_neu):
        WFSch_Stufe_Mitarbeiter_Immer_Erforderlich.objects.using(projekt.db_bezeichnung()).create(
            wfsch_stufe_mitarbeiter = self,
            immer_erforderlicht = immer_erforderlich_neu,
            zeitstempel = timezone.now()
            )
    
    def immer_erforderlich(self, projekt):
        try:
            qs_wfschSt_ma_immer_erf = WFSch_Stufe_Mitarbeiter_Immer_Erforderlich.objects.using(projekt.db_bezeichnung()).filter(wfsch_stufe_mitarbeiter = self)
            return qs_wfschSt_ma_immer_erf.latest('zeitstempel').immer_erforderlich
        except ObjectDoesNotExist:
            return False

class WFSch_Stufe_Mitarbeiter_Aktuell(models.Model):
    wfsch_stufe_mitarbeiter = models.ForeignKey(WFSch_Stufe_Mitarbeiter, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class WFSch_Stufe_Mitarbeiter_Immer_Erforderlich(models.Model):
    wfsch_stufe_mitarbeiter = models.ForeignKey(WFSch_Stufe_Mitarbeiter, on_delete = models.CASCADE)
    immer_erforderlich = models.BooleanField()
    zeitstempel = models.DateTimeField()

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
    def bezeichnung_ändern(self, projekt, neue_bezeichnung):
        Ordner_Bezeichnung.objects.using(projekt.db_bezeichnung()).create(
            ordner = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )
        
    def bezeichnung(self, projekt):
        return Ordner_Bezeichnung.objects.using(projekt.db_bezeichnung()).filter(ordner = self).latest('zeitstempel').bezeichnung

    # ORDNER VERBINDUNG WFSCH
    def verbindung_wfsch_herstellen(self, projekt, wfsch):
        verbindung_ordner_wfsch = Ordner_WFSch.objects.using(projekt.db_bezeichnung()).get_or_create(
            ordner = self,
            wfsch = wfsch,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_ordner_wfsch.aktualisieren(projekt)

    def verbindung_wfsch_löschen(self, projekt):
        try:
            verbindung_ordner_wfsch = Ordner_WFSch.objects.using(projekt.db_bezeichnung()).filter(ordner = self).latest('zeitstempel')
            verbindung_ordner_wfsch.entaktualisieren(projekt)
        except ObjectDoesNotExist:
            pass

    def wfsch(self, projekt):
        try:
            verbindung_o_wfsch = Ordner_WFSch.objects.using(projekt.db_bezeichnung()).filter(ordner = self).latest('zeitstempel')
            if verbindung_o_wfsch.aktuell(projekt) and not verbindung_o_wfsch.wfsch.gelöscht(projekt):
                return verbindung_o_wfsch.wfsch
        except ObjectDoesNotExist:
            return None

    # ORDNER VERBINDUNG ROLLE
    def verbindung_rolle_herstellen(self, projekt, rolle):
        verbindung_ordner_rolle = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get_or_create(
            ordner = self,
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )
        verbindung_ordner_rolle.aktualisieren(projekt)

    def verbindung_rolle_lösen(self, projekt, rolle):
        verbindung_ordner_rolle = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get(
            ordner = self,
            rolle = rolle,
            )
        verbindung_ordner_rolle.entaktualisieren(projekt)

    # ORDNER LESEFREIGABE ROLLE
    def lesefreigabe_erteilen_rolle(self, projekt, rolle):
        o_ro = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get_or_create(
            ordner = self, 
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        Freigabe_Lesen_Rolle.objects.using(projekt).create(
            ordner_rolle = o_ro,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )
    
    def lesefreigabe_entziehen_rolle(self, projekt, rolle):
        o_ro = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get(ordner = self, rolle = rolle)
        Freigabe_Lesen_Rolle.objects.using(projekt.db_bezeichnung()).create(
            ordner_rolle = o_ro,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_rolle(self, projekt, rolle):
        try:
            o_ro = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get(ordner = self, rolle = rolle)
            return Freigabe_Lesen_Rolle.objects.using(projekt.db_bezeichnung()).filter(ordner_rolle = o_ro).latest('zeitstempel').freigabe_lesen
        except ObjectDoesNotExist:
            return False

    # ORDNER UPLOADFREIGABE ROLLE
    def uploadfreigabe_erteilen_rolle(self, projekt, rolle):
        o_ro = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get_or_create(
            ordner = self, 
            rolle = rolle,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        Freigabe_Upload_Rolle.objects.using(projekt.db_bezeichnung()).create(
            ordner_rolle = o_ro, 
            freigabe_upload = True, 
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen_rolle(self, projekt, rolle):
        o_ro = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get(ordner = self, rolle = rolle)
        Freigabe_Upload_Rolle.objects.using(projekt.db_bezeichnung()).create(
            ordner_rolle = o_ro, 
            freigabe_upload = False, 
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_rolle(self, projekt, rolle):
        try:
            o_ro = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get(ordner = self, rolle = rolle)
            return Freigabe_Upload_Rolle.objects.using(projekt.db_bezeichnung()).filter(ordner_rolle = o_ro).latest('zeitstempel').freigabe_upload
        except ObjectDoesNotExist:
            return False

    # ORDNER FREIGABEN VORLAGE
    def vorlage(self, projekt):
        try:
            verbindung_vorlage = Ordner_Vorlage.objects.using(projekt.db_bezeichnung()).get(ordner = self)
            return V_Ordner.objects.using(DB_SUPER).get(pk = verbindung_vorlage.v_ordner_id)
        except ObjectDoesNotExist:
            return None

    def freigaben_von_vorlage_übernehmen(self, projekt):
        v_ordner = self.vorlage(projekt)
        for v_r in v_ordner.liste_rollen():
            # Rolle wenn nötig in DB anlegen
            try:
                rolle = Rolle_Vorlage.objects.using(db_bezeichnung_ziel).get(v_rolle_id = v_r.id).rolle
            except ObjectDoesNotExist:
                rolle = v_r.in_db_anlegen(db_bezeichnung_quelle, db_bezeichnung_ziel)
            # Verbindung Ordner Rolle herstellen
            ordner_rolle = Ordner_Rolle.objects.using(projekt.db_bezeichnung()).get_or_create(
                ordner = self,
                rolle = rolle,
                defaults = {'zeitstempel':timezone.now()}
                )[0]
            ordner_rolle.aktualisieren(projekt)
            # Freigaben übernehmen
            if v_ordner.freigabe_lesen(v_rolle = v_r):
                self.lesefreigabe_erteilen_rolle(projekt, rolle = rolle)
            else:
                self.lesefreigabe_entziehen_rolle(projekt, rolle = rolle)
            if v_ordner.freigabe_upload(v_rolle = v_r):
                self.uploadfreigabe_erteilen_rolle(projekt, rolle = rolle)
            else:
                self.uploadfreigabe_entziehen_rolle(projekt, rolle = rolle)
    
    # ORDNER LESEFREIGABE FIRMA
    def lesefreigabe_erteilen_firma(self, projekt, firma):
        o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
            ordner = self, 
            firma_id = firma.id,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        Freigabe_Lesen_Firma.objects.using(projekt.db_bezeichnung()).create(
            ordner_firma = o_fa,
            freigabe_lesen = True,
            zeitstempel = timezone.now()
            )
        # Uploadfreigabe entziehen (gleichzeitige Lese- und Uploadfreigabe vermeiden)
        Freigabe_Upload_Firma.objects.using(projekt.db_bezeichnung()).create(
            ordner_firma = o_fa,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_entziehen_firma(self, projekt, firma):
        o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get(ordner = self, firma_id = firma.id)
        Freigabe_Lesen_Firma.objects.using(projekt.db_bezeichnung()).create(
            ordner_firma = o_fa,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def lesefreigabe_firma(self, projekt, firma):
        try:
            o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get(ordner = self, firma_id = firma.id)
            return Freigabe_Lesen_Firma.objects.using(projekt.db_bezeichnung()).filter(ordner_firma = o_fa).latest('zeitstempel').freigabe_lesen
        except ObjectDoesNotExist:
            return False

    # ORDNER UPLOADFREIGABE FIRMA
    def uploadfreigabe_erteilen_firma(self, projekt, firma):
        o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
            ordner = self, 
            firma_id = firma.id,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        Freigabe_Upload_Firma.objects.using(projekt.db_bezeichnung()).create(
            ordner_firma = o_fa,
            freigabe_upload = True,
            zeitstempel = timezone.now()
            )
        # Lesefreigabe entziehen (gleichzeitige Lese- und Uploadfreigabe vermeiden)
        Freigabe_Lesen_Firma.objects.using(projekt.db_bezeichnung()).create(
            ordner_firma = o_fa,
            freigabe_lesen = False,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_entziehen_firma(self, projekt, firma):
        o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get(ordner = self, firma_id = firma.id)
        Freigabe_Upload_Firma.objects.using(projekt.db_bezeichnung()).create(
            ordner_firma = o_fa,
            freigabe_upload = False,
            zeitstempel = timezone.now()
            )

    def uploadfreigabe_firma(self, projekt, firma):
        try:
            o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get(ordner = self, firma_id = firma.id)
            return Freigabe_Upload_Firma.objects.using(projekt.db_bezeichnung()).filter(ordner_firma = o_fa).latest('zeitstempel').freigabe_upload
        except ObjectDoesNotExist:
            return False

    # ORDNER ALLE FREIGABEN
    def freigaben_übertragen_rollen_firma(self, projekt, firma):
        self.freigaben_entziehen_firma(projekt, firma)
        for rolle in liste_rollen_firma(projekt, firma):
            if self.lesefreigabe_rolle(projekt, rolle) and not self.lesefreigabe_firma(projekt, firma) and not self.uploadfreigabe_firma(projekt, firma):
                self.lesefreigabe_erteilen_firma(projekt, firma)
            if self.uploadfreigabe_rolle(projekt, rolle) and not self.uploadfreigabe_firma(projekt, firma):
                self.uploadfreigabe_erteilen_firma(projekt, firma)
    
    def freigaben_entziehen_firma(self, projekt, firma):
        try:
            o_fa = Ordner_Firma.objects.using(projekt.db_bezeichnung()).get(ordner = self, firma_id = firma.id)
            Freigabe_Lesen_Firma.objects.using(projekt.db_bezeichnung()).create(
                ordner_firma = o_fa,
                freigabe_lesen = False,
                zeitstempel = timezone.now()
                )
            Freigabe_Upload_Firma.objects.using(projekt.db_bezeichnung()).create(
                ordner_firma = o_fa,
                freigabe_upload = False,
                zeitstempel = timezone.now()
                )        
        except ObjectDoesNotExist:
            pass

    # ORDNER UNTERORDNER
    def unterordner_anlegen(self, projekt, bezeichnung_unterordner):
        neuer_unterordner = Ordner.objects.using(projekt.db_bezeichnung()).create(
            zeitstempel = timezone.now(),
            ist_root_ordner = False,
            )
        neuer_unterordner.bezeichnung_ändern(projekt, bezeichnung_unterordner)
        neuer_unterordner.entlöschen(projekt)
        # Verbindung Ordner-Unterordner anlegen
        self.unterordner_verbinden(projekt, neuer_unterordner)

    def unterordner_verbinden(self, projekt, unterordner):
        verbindung_o_uo = Ordner_Unterordner.objects.using(projekt.db_bezeichnung()).create(
            ordner = self,
            unterordner = unterordner,
            zeitstempel = timezone.now()
            )
        verbindung_o_uo.aktualisieren(projekt)

    def liste_unterordner(self, projekt):
        qs_verbindungen_o_uo = Ordner_Unterordner.objects.using(projekt.db_bezeichnung()).filter(ordner = self)
        li_unterordner = []
        for verbindung_o_uo in qs_verbindungen_o_uo:
            if verbindung_o_uo.aktuell(projekt) and not verbindung_o_uo.unterordner.gelöscht(projekt):
                li_unterordner.append(verbindung_o_uo.unterordner)
        return li_unterordner

    def _liste_unterordner_dict(self, projekt, mitarbeiter):
        li_uo_dict = []
        for uo in self.liste_unterordner(projekt):
            li_uo_dict.append(uo.ordner_dict(projekt, mitarbeiter))
        return li_uo_dict

    def _listendarstellung_ordnerbaum_unterhalb(self, projekt, mitarbeiter):
        li_listendarstellung = []
        def rekursion_liste_uo(ordner):
            li_listendarstellung.append(ordner.ordner_dict(projekt, mitarbeiter))
            for uo in ordner.liste_unterordner(projekt):
                rekursion_liste_uo(uo)
        
        rekursion_liste_uo(self)
        return li_listendarstellung

    # ORDNER ÜBERORDNER
    def überordner(self, projekt):
        qs_verbindungen_üo_o = Ordner_Unterordner.objects.using(projekt.db_bezeichnung()).filter(unterordner = self)
        if qs_verbindungen_üo_o:
            jüngste_verbindung_üo_o = qs_verbindungen_üo_o.latest('zeitstempel')
            if jüngste_verbindung_üo_o.aktuell(projekt) and not jüngste_verbindung_üo_o.ordner.gelöscht(projekt):
                return jüngste_verbindung_üo_o.ordner
        else:
            return None

    # ORDNER EBENE
    def ebene(self, projekt):
        o = self
        ebene = 0
        while o.überordner(projekt):
            ebene += 1
            o = o.überordner(projekt)
        return ebene

    # ORDNER LÖSCHEN
    def löschen(self, projekt):
    # Verbindungen zu Über-/ Unterordnern werden nicht mitgelöscht, sonst fehlen sie wenn Ordner wieder entlöscht wird
        # Ornder löschen
        Ordner_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
                    ordner = self,
                    gelöscht = True, 
                    zeitstempel = timezone.now()
                    )
        # Unterliegenden Ordnerbaum mitlöschen
        def rekursion_ordnerbaum_löschen(ordner):
            for uo in ordner.liste_unterordner(projekt):
                rekursion_ordnerbaum_löschen(uo)
                Ordner_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
                    ordner = uo,
                    gelöscht = True, 
                    zeitstempel = timezone.now()
                    )
        
        rekursion_ordnerbaum_löschen(self)
        # TODO: Prüfen ob Dokumente, Unterordner etc. verknüpft
        # TODO: Unterliegenden Ordnerbaum mitlöschen

    def entlöschen(self, projekt):
        Ordner_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            ordner = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self, projekt):
        return Ordner_Gelöscht.objects.using(projekt.db_bezeichnung()).filter(ordner = self).latest('zeitstempel').gelöscht

    # ORDNER DOKUMENTE
    def _dokument_anlegen(self, projekt, mitarbeiter, formulardaten, liste_dateien):
        neues_dokument = Dokument.objects.using(projekt.db_bezeichnung()).create(
            mitarbeiter = mitarbeiter,
            zeitstempel = timezone.now()
            )
        neues_dokument.bezeichnung_ändern(projekt, neue_bezeichnung = formulardaten['dokument_bezeichnung'])
        neues_dokument.entlöschen(projekt)

        # Neue Verbindung Dokument-Ordner anlegen
        Dokument_Ordner.objects.using(projekt.db_bezeichnung()).create(
            dokument = neues_dokument,
            ordner = self,
            zeitstempel = timezone.now()
            )

        # Dateien hochladen und anlegen:
        for datei in liste_dateien:
            neues_dokument._datei_anlegen(projekt, f = datei)

        # TODO: Workflow initiieren

    def _liste_dokumente(self, projekt):
        qs_dok_ord = Dokument_Ordner.objects.using(projekt.db_bezeichnung()).filter(ordner = self)
        li_dok = []
        for dok_ord in qs_dok_ord:
            if not dok_ord.dokument.gelöscht(projekt):
                li_dok.append(dok_ord.dokument)
        return li_dok

    def _liste_dokumente_dict(self, projekt):
        li_dok_dict = []
        for dok in self._liste_dokumente(projekt):
            li_dok_dict.append(dok._dokument_dict(projekt))
        return li_dok_dict

    def _liste_dokumente_freigegeben(self, projekt):
        qs_dok_ord = Dokument_Ordner.objects.using(projekt.db_bezeichnung()).filter(ordner = self)
        li_dok_frei = []
        for dok_ord in qs_dok_ord:
            if not dok_ord.dokument.gelöscht(projekt) and dok_ord.dokument.freigegeben(projekt):
                li_dok_frei.append(dok_ord.dokument)
        return li_dok_frei

    def _liste_dokumente_freigegeben_dict(self, projekt):
        li_dok_frei_dict = []
        for dok in self._liste_dokumente_freigegeben(projekt):
            li_dok_frei_dict.append(dok._dokument_dict(projekt))
        return li_dok_frei_dict

    def _liste_dokumente_mitarbeiter(self, projekt, mitarbeiter):
        qs_dok_ord = Dokument_Ordner.objects.using(projekt.db_bezeichnung()).filter(ordner = self)
        li_dok_ma = []
        for dok_ord in qs_dok_ord:
            if not dok_ord.dokument.gelöscht(projekt) and dok_ord.dokument.mitarbeiter == mitarbeiter:
                li_dok_ma.append(dok_ord.dokument)
        return li_dok_ma

    def _liste_dokumente_mitarbeiter_dict(self, projekt, mitarbeiter):
        li_dok_ma_dict = []
        for dok in self._liste_dokumente_mitarbeiter(projekt, mitarbeiter):
            li_dok_ma_dict.append(dok._dokument_dict(projekt))
        return li_dok_ma_dict

    def ordner_dict(self, projekt, mitarbeiter):
        dict_o = self.__dict__
        dict_o['bezeichnung'] = self.bezeichnung(projekt)
        dict_o['freigabe_upload'] = self.uploadfreigabe_firma(projekt, mitarbeiter.firma)
        dict_o['freigabe_lesen'] = self.lesefreigabe_firma(projekt, mitarbeiter.firma)

        # Ordnerebene (oberste Ebene, also die direkt unter ROOT-Ordner, ist Ebene '0')
        ebene = 0
        o = self
        while o.überordner(projekt):
            ebene += 1
            o = o.überordner(projekt)
        dict_o['ebene'] = ebene
        
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
    def aktualisieren(self, projekt):
        Ordner_Unterordner_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            ordner_unterordner = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, projekt):
        Ordner_Unterordner_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            ordner_unterordner = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        return Ordner_Unterordner_Aktuell.objects.using(projekt.db_bezeichnung()).filter(ordner_unterordner = self).latest('zeitstempel').aktuell

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

    def aktualisieren(self, projekt):
        Ordner_Rolle_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            ordner_rolle = self,
            aktuell = True, 
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        return Ordner_Rolle_Aktuell.objects.using(projekt.db_bezeichnung()).filter(ordner_rolle = self).latest('zeitstempel').aktuell

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

    def aktualisieren(self, projekt):
        Ordner_WFSch_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            ordner_wfsch = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, projekt):
        Ordner_WFSch_Aktuell.objects.using(projekt.db_bezeichnung()).create(
            ordner_wfsch = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, projekt):
        return Ordner_WFSch_Aktuell.objects.using(projekt.db_bezeichnung()).filter(ordner_wfsch = self).latest('zeitstempel').aktuell

class Ordner_WFSch_Aktuell(models.Model):
    ordner_wfsch = models.ForeignKey(Ordner_WFSch, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Projektstruktur(models.Model):
    zeitstempel = models.DateTimeField()
    v_pjs_id = models.CharField(max_length = 20)


#####################################
# DOKUMENTE

class Dokument(models.Model):
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

    # DOKUMENT BEZEICHNUNG
    def _bezeichnung_ändern(self, projekt, bezeichnung_neu):
        Dokument_Bezeichnung.objects.using(projekt.db_bezeichnung()).create(
            dokument = self,
            bezeichnung = bezeichnung_neu,
            zeitstempel = timezone.now()
            )
    
    def _bezeichnung(self, projekt):
        return Dokument_Bezeichnung.objects.using(projekt.db_bezeichnung()).filter(dokument = self).latest('zeitstempel').bezeichnung

    # DOKUMENT GELÖSCHT
    def _löschen(self, projekt):
        Dokument_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            dokument = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def _entlöschen(self, projekt):
        Dokument_Gelöscht.objects.using(projekt.db_bezeichnung()).create(
            dokument = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def _gelöscht(self, projekt):
        return Dokument_Gelöscht.objects.using(projekt.db_bezeichnung()).filter(dokument = self).latest('zeitstempel').gelöscht

    # DOKUMENT FREIGEGEBEN
    def _freigabe_erteilen(self, projekt):
        Dokument_Freigegeben.objects.using(projekt.db_bezeichnung()).create(
            dokument = self,
            freigegeben = True,
            zeitstempel = timezone.now()
            )

    def _freigegeben(self, projekt):
        try:
            return Dokument_Freigegeben.objects.using(projekt.db_bezeichnung()).filter(dokument = self).latest('zeitstempel').freigegeben
        except ObjectDoesNotExist:
            return False

    # DOKUMENT ORDNER
    def _ordner_ändern(self, projekt, ordner_neu):
        dokument_ordner_neu = Dokument_Ordner.objects.using(projekt.db_bezeichnung()).create(
            dokument = self,
            ordner = ordner_neu,
            zeitstempel = timezone.now()
            )
        
    def _ordner(self, projekt):
        # Dokument hat immer nur einen Ordner --> letzter Ordner wird zurückgegeben
        return Dokument_Ordner.objects.using(projekt.db_bezeichnung()).filter(dokument = self).latest('zeitstempel').ordner

    # DOKUMENT DATEIEN
    def _datei_anlegen(self, projekt, f):
        projektpfad = Pfad.objects.using(projekt.db_bezeichnung()).latest('zeitstempel').pfad        
        neue_datei = Datei(
            dateiname = f.name,
            pfad = projektpfad,
            zeitstempel = timezone.now()
            )
        # Verbindung Dokument-Datei anlegen
        neue_verbindung_dok_dat = Dokument_Datei(
            dokument = self,
            datei = neue_datei,
            zeitstempel = timezone.now()
            )
        # Datei hochladen
        neue_datei._hochladen(projekt, f)
        # Wenn Datei erfolreich hochgeladen --> Einträge in DB speichern
        neue_datei.save(using = projekt.db_bezeichnung())
        neue_verbindung_dok_dat.save(using = projekt.db_bezeichnung())

    def _liste_dateien(self, projekt):
        qs_dokument_datei = Dokument_Datei.objects.using(projekt.db_bezeichnung()).filter(dokument = self)
        li_dateien = []
        for dok_dat in qs_dokument_datei:
            li_dateien.append(dok_dat.datei)
        return li_dateien
    
    def _liste_dateien_dict(self, projekt):
        li_dateien_dict = []
        for dat in self._liste_dateien(projekt):
            li_dateien_dict.append(dat.__dict__)
        return li_dateien_dict

    # DOKUMENT KOMMENTARE
    def _kommentar_anlegen(self, projekt, mitarbeiter, kommentartext_neu, liste_dateien):
        neues_kommentar = Kommentar.objects.using(projekt.db_bezeichnung()).create(
            mitarbeiter = mitarbeiter,
            kommentartext = kommentartext_neu,
            zeitstempel = timezone.now()
            )
        # Verbindung Dokument-Kommentar anlegen
        Dokument_Kommentar.objects.using(projekt.db_bezeichnung()).create(
            dokument = self,
            kommentar = neues_kommentar,
            zeitstempel = timezone.now()
            )
        
        # TODO: liste_dateien bearbeiten: Hochladen, Dateien anlegen, Verbindungen Kommentar-Datei anlegen

    def _liste_kommentare(self, projekt):
        qs_dok_kom = Dokument_Kommentar.objects.using(projekt.db_bezeichnung()).filter(dokument = self)
        li_kommentare = []
        for dok_kom in qs_dok_kom:
            li_kommentare.append(dok_kom.kommentar)
        return li_kommentare

    def _liste_kommentare_dict(self, projekt):
        li_kommentare_dict = []
        for k in self._liste_kommentare(projekt):
            dict_k = k.__dict__
            dict_k['liste_dateien'] = k._liste_dateien_dict(projekt)
            li_kommentare_dict.append(dict_k)
        return li_kommentare_dict

    # DOKUMENT DICT
    def _dokument_dict(self, projekt):
        dict_dok = self.__dict__
        dict_dok['bezeichnung'] = self._bezeichnung(projekt)
        dict_dok['mitarbeiter'] = self.mitarbeiter.mitarbeiter_dict()
        dict_dok['status'] = 'FREIGABESTATUS NOCHT IMPLEMENTIEREN'

class Dokument_Bezeichnung(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class Dokument_Gelöscht(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Dokument_Freigegeben(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    freigegeben = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Dokument_Ordner(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    ordner = models.ForeignKey(Ordner, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Pfad(models.Model):
    pfad = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()

class Datei(models.Model):
# Dateien auch als Anhang für Kommentar etc. einsetzbar ==> Verbindungen über Through-Tabellen zwecks Flexibilität
    dateiname = models.CharField(max_length = 50)
    pfad = models.ForeignKey(Pfad, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # DATEI HOCHLADEN
    def _hochladen(self, projekt, f):
        projektpfad = Pfad.objects.using(projekt.db_bezeichnung()).latest('zeitstempel').pfad
        dateipfad = projektpfad + self.id
        ziel = open(dateipfad, 'wb+')
        for chunk in f.chunks():
            ziel.write(chunk)
        ziel.close()

class Dokument_Datei(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    datei = models.ForeignKey(Datei, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Kommentar(models.Model):
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    kommentartext = models.CharField(max_length = 250)
    zeitstempel = models.DateTimeField()

    # KOMMENTAR DATEIEN
    def _datei_anlegen(self, projekt, daten_datei_neu):
        pass

    def _liste_dateien(self, projekt):
        qs_kom_dat = Kommentar_Datei.objects.using(projekt.db_bezeichnung()).filter(kommentar = self)
        li_dateien = []
        for kom_dat in qs_kom_dat:
            li_dateien.append(kom_dat.datei)
    
    def _liste_dateien_dict(self, projekt):
        li_dateien_dict = []
        for dat in self._liste_dateien(projekt):
            li_dateien_dict.append(dat.__dict__)
        return li_dateien_dict

class Kommentar_Datei(models.Model):
    kommentar = models.ForeignKey(Kommentar, on_delete = models.CASCADE)
    datei = models.ForeignKey(Datei, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Dokument_Kommentar(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    kommentar = models.ForeignKey(Kommentar, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

###################################################################
# FUNKTIONEN OHNE KLASSE

# ROLLEN
def liste_rollen(projekt):
    li_rollen = []
    for r in Rolle.objects.using(projekt.db_bezeichnung()).all():
        if not r.gelöscht(projekt):
            li_rollen.append(r)
    return li_rollen

def liste_rollen_dict(projekt):
    li_rollen_dict = []
    for r in liste_rollen(projekt):
        li_rollen_dict.append(r.dict_rolle(projekt))
    return li_rollen_dict

def liste_rollen_mitarbeiter(projekt, mitarbeiter):
    li_rollen_ma = []
    for r in liste_rollen(projekt):
        if r.mitarbeiter_ist_rolleninhaber(projekt, mitarbeiter):
            li_rollen_ma.append(r)
        
    return li_rollen_ma

def liste_rollen_mitarbeiter_dict(projekt, mitarbeiter):
    li_rollen_ma_dict = []
    for r in liste_rollen_mitarbeiter(projekt, mitarbeiter):
        li_rollen_ma_dict.append(r.dict_rolle(projekt))
    return li_rollen_ma_dict

def liste_rollen_firma(projekt, firma):
    qs_verbindungen_rolle_firma = Rolle_Firma.objects.using(projekt.db_bezeichnung()).filter(firma_id = firma.id)
    li_rollen_firma = []
    for verbindung_rolle_firma in qs_verbindungen_rolle_firma:
        if verbindung_rolle_firma.aktuell(projekt) and not verbindung_rolle_firma.rolle.gelöscht(projekt):
            li_rollen_firma.append(verbindung_rolle_firma.rolle)
    return li_rollen_firma

def liste_rollen_firma_dict(projekt, firma):
    li_rollen_firma_dicts = []
    for r in liste_rollen_firma(projekt, firma):
        dict_ro = r.dict_rolle(projekt)
        dict_ro['liste_rolleninhaber'] = r.liste_rolleninhaber_firma_dict(projekt, firma)
        dict_ro['liste_nicht_rolleninhaber'] = r.liste_nicht_rolleninhaber_firma_dict(projekt, firma)
        li_rollen_firma_dicts.append(dict_ro)
    return li_rollen_firma_dicts

def firma_projektrollen_zuweisen(projekt, firma, formulardaten):
    for r in liste_rollen(projekt):
        ist_firmenrolle = True if str(r.id) in formulardaten else False
        r.ist_firmenrolle_ändern(projekt, firma, ist_firmenrolle)

def firma_rolle_zuweisen(projekt, firma, rolle):
    verbindung_ro_fa = Rolle_Firma.objects.using(projekt.db_bezeichnung()).get_or_create(
        rolle = rolle, 
        firma_id = firma.id,
        defaults = {'zeitstempel': timezone.now()}
        )
    verbindung_ro_fa.aktualisieren(projekt)

# FIRMA
def firma_liste_mitarbeiter_projekt(projekt, firma):
# Gibt Liste der Projektmitarbeiter für projekt zurück, die zu firma gehören
    firma_li_ma_pj = []
    for ma in firma.liste_mitarbeiter():
        if projekt in liste_projekte_mitarbeiter(ma):
            firma_li_ma_pj.append(ma)
    return firma_li_ma_pj

def firma_liste_mitarbeiter_projekt_dict(projekt, firma):
    firma_li_ma_pj_dict = []
    for ma in firma_liste_mitarbeiter_projekt(projekt, firma):
        dict_ma = ma.mitarbeiter_dict()
        dict_ma['ist_projektadmin'] = ma.ist_projektadmin(projekt)
        firma_li_ma_pj_dict.append(dict_ma)
    return firma_li_ma_pj_dict

def firma_liste_wfsch(projekt, firma):
    li_wfsch = []
    for wfsch in liste_wfsch(projekt):
        for wfsch_st in wfsch.liste_stufen(projekt):
            if firma in wfsch_st.liste_prüffirmen(projekt):
                if wfsch not in li_wfsch:
                    li_wfsch.append(wfsch)
    return li_wfsch

def firma_liste_wfsch_dict(projekt, firma):
    li_wfsch_dict = []
    for wfsch in firma_liste_wfsch(projekt, firma):
        li_wfsch_dict.append(wfsch.wfsch_dict(projekt, firma))
    return li_wfsch_dict

# MITARBEITER
def liste_projekte_mitarbeiter(mitarbeiter):
    # Vorauswahl: Liste der Firmenprojekte
    li_pj_fa = mitarbeiter.firma.liste_projekte()
    
    # Wenn Mitarbeiter mit einer Rolle im Projekt verbunden ist, dann Projekt hinzufügen
    li_pj_ma = []
    for pj in li_pj_fa:
        qs_verbindungen_ro_ma = Rolle_Mitarbeiter.objects.using(pj.db_bezeichnung()).filter(mitarbeiter_id = mitarbeiter.id)
        for verbindung_ro_ma in qs_verbindungen_ro_ma:
            if verbindung_ro_ma.aktuell(pj):
                # Wenn Firma nicht mehr mit Rolle verbunden oder Rolle gelöscht, dann wird Projekt nicht hinzugefügt
                verbindung_ro_fa = verbindung_ro_ma.rolle_firma
                if verbindung_ro_fa.aktuell(pj) and not verbindung_ro_fa.rolle.gelöscht(pj):
                    # Projekt nur hinzufügen, wenn nicht bereits in der Liste
                    if not pj in li_pj_ma:
                        li_pj_ma.append(pj)
    
    return li_pj_ma

def liste_projekte_mitarbeiter_dict(mitarbeiter):
# Mitarbeiter ist über Rolle mit Projekt verbunden
    li_pj_ma_dict = []
    for pj in liste_projekte_mitarbeiter(mitarbeiter):
        pj_ma_dict = pj.projekt_dict()
        pj_ma_dict['mitarbeiter_ist_projektadmin'] = None
        pj_ma_dict['liste_rollen'] = liste_rollen_mitarbeiter_dict(pj, mitarbeiter)
        li_pj_ma_dict.append(pj_ma_dict)

    return li_pj_ma_dict

def mitarbeiter_ist_projektmitarbeiter(mitarbeiter, projekt):
    if projekt in liste_projekte_mitarbeiter(mitarbeiter):
        return True
    return False

# ORDNER
def liste_oberste_ordner(projekt):
    li_oberste_o = []
    for o in Ordner.objects.using(projekt.db_bezeichnung()).all():
        if o.ebene(projekt) == 0 and not o.gelöscht(projekt):
            li_oberste_o.append(o)
    return li_oberste_o

def liste_oberste_ordner_dict(projekt, mitarbeiter):
    li_ober_o_dict = []
    for ober_o in liste_oberste_ordner(projekt):
        li_ober_o_dict.append(ober_o.ordner_dict(projekt, mitarbeiter))
    return li_ober_o_dict

def liste_oberste_v_ordner(projekt):
    li_oberste_v_o = []
    for v_o in V_Ordner.objects.using(projekt.db_bezeichnung()).all():
        if v_o.ebene(projekt) == 0 and not v_o.gelöscht(projekt):
            li_oberste_v_o.append(v_o)
    return li_oberste_v_o

def liste_ordner(projekt):
    # Ordnerliste, sortiert nach Ordnerbaum
    li_ordner = []
    def rekursion_uo_anhängen(o):
        for uo in o.liste_unterordner(projekt):
            li_ordner.append(uo)
            rekursion_uo_anhängen(uo)
    
    for oberster_ordner in liste_oberste_ordner(projekt):
        li_ordner.append(oberster_ordner)
        rekursion_uo_anhängen(oberster_ordner)

    return li_ordner

def liste_ordner_dict(projekt):
    li_ordner_dict = []
    for o in liste_ordner(projekt):
        li_ordner_dict.append(o.ordner_dict(projekt))
    return li_ordner_dict

def listendarstellung_ordnerbaum_gesamt(projekt, mitarbeiter):
    li_listendarstellung_gesamt = []
    for ober_o in liste_oberste_ordner(projekt):
        for dict_o in ober_o._listendarstellung_ordnerbaum_unterhalb(projekt, mitarbeiter):
            li_listendarstellung_gesamt.append(dict_o)
    return li_listendarstellung_gesamt

# WFSCH
def liste_wfsch(projekt):
    li_wfsch = []
    for wfsch in Workflow_Schema.objects.using(projekt.db_bezeichnung()).all():
        if not wfsch.gelöscht(projekt):
            li_wfsch.append(wfsch)
    return li_wfsch

def liste_wfsch_dict(projekt):
    li_wfsch_dict = []
    for wfsch in liste_wfsch(projekt):
        li_wfsch_dict.append(wfsch.wfsch_dict(projekt))
    return li_wfsch_dict

# PJS
def liste_v_pjs():
    li_v_pjs = []
    for v_pjs in V_Projektstruktur.objects.using(DB_SUPER).all():
        if not v_pjs.gelöscht(): 
            li_v_pjs.append(v_pjs)
    return li_v_pjs

def liste_v_pjs_dict():
    li_v_pjs_dict = []
    for v_pjs in liste_v_pjs():
        li_v_pjs_dict.append(v_pjs.v_pjs_dict())
    return li_v_pjs_dict

# DATEIEN


#
###################################################################

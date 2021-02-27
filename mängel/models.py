from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.fields import CharField, DateTimeField
from django.utils import timezone

from projektadmin.models import Status, Datei
from superadmin.models import Firma
from gernotbau.settings import DB_SUPER

class Ticket(models.Model):
    aussteller_id = CharField(max_length = 20)
    zeitstempel = DateTimeField()

    # TICKET GELÖSCHT
    def _löschen(self, pj):
        Ticket_Gelöscht.objects.using(pj.db_bezeichnung()).create(
            ticket = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def _entlöschen(self, pj):
        Ticket_Gelöscht.objects.using(pj.db_bezeichnung()).create(
            ticket = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def _gelöscht(self, pj):
        try:
            return Ticket_Gelöscht.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel').gelöscht
        except ObjectDoesNotExist:
            return False

    # TICKET BEZEICHNUNG
    def _bezeichnung_ändern(self, pj, bezeichnung_neu):
        Ticket_Bezeichnung.objects.using(pj.db_bezeichnung()).create(
            ticket = self,
            bezeichnung = bezeichnung_neu,
            zeitstempel = timezone.now(),
            )
    
    def _bezeichnung(self, pj):
        return Ticket_Bezeichnung.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel').bezeichnung

    # TICKET X-KOORDINATE
    def _x_koordinate_ändern(self, pj, plan, x_koordinate_neu):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        Ticket_Plan_X.objects.using(pj.db_bezeichnung()).create(
            ticket_plan = ti_pl,
            x_koordinate = x_koordinate_neu,
            zeitstempel = timezone.now()
            )
    
    def _x_koordinate(self, pj, plan):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        return Ticket_Plan_X.objects.using(pj.db_bezeichnung()).filter(ticket_plan = ti_pl).latest('zeitstempel').x_koordinate

    # TICKET Y-KOORDINATE
    def _y_koordinate_ändern(self, pj, plan, y_koordinate_neu):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        Ticket_Plan_Y.objects.using(pj.db_bezeichnung()).create(
            ticket_plan = ti_pl,
            y_koordinate = y_koordinate_neu,
            zeitstempel = timezone.now()
            )
    
    def _y_koordinate(self, plan, pj):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        return Ticket_Plan_Y.objects.using(pj.db_bezeichnung()).filter(ticket_plan = ti_pl).latest('zeitstempel').y_koordinate

    # TICKET EMPFÄNGERGIRMA
    def _empfängerfirma_hinzufügen(self, pj, empfängerfirma_id):
        ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).create(
            ticket = self,
            firma_id = empfängerfirma_id,
            zeitstempel = timezone.now()
            )
        return ti_empf

    def _liste_empfängerfirmen(self, pj):
        li_empf = []
        qs_ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self)
        for ti_empf in qs_ti_empf:
            empf = Firma.objects.using(DB_SUPER).get(pk = ti_empf.firma_id)
            if ti_empf.aktuell(pj) and not empf.gelöscht():
                li_empf.append(empf)
        return li_empf

    # TICKET DICT
    def _dict_für_übersicht(self, pj):
        dict_ticket = self.__dict__
        dict_ticket['bezeichnung'] = None
        dict_ticket['fälligkeit'] = None
        dict_ticket['status_aussteller'] = None
        dict_ticket['plan']
        
        # Liste Empfänger
        li_empf = []
        for ti_empf in Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self):
            if ti_empf.aktuell(pj):
                empf = Firma.objects.using(DB_SUPER).get(pk = ti_empf.firma_id)
                dict_empf = empf.__dict__
                dict_empf['bezeichnung'] = empf._bezeichnung()
                dict_empf['status'] = ti_empf._status(pj)
                dict_empf['gelesen'] = ti_empf._gelesen(pj)
                li_empf.append(dict_empf)

        dict_ticket['liste_empfänger'] = None # Status, Gelesen

        return dict_ticket

class Ticket_Gelöscht(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ticket_Bezeichnung(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 25)
    zeitstempel = models.DateTimeField()

class Ticket_Fälligkeitsdatum(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    zeitstempel = DateTimeField()
    fälligkeitsdatum = DateTimeField()

class Ticket_Ausstellerstatus(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    status = models.ForeignKey(Status, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Empfängerfirma(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

    # TICKET_EMPFÄNGERFIRMA AKTUELL
    def _aktualisieren(self, pj):
        Ticket_Empfängerfirma_Aktuell.objects.using(pj.db_bezeichnung()).create(
            ticket_empfängerfirma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def _entaktualisieren(self, pj):
        Ticket_Empfängerfirma_Aktuell.objects.using(pj.db_bezeichnung()).create(
            ticket_empfängerfirma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )
    
    def _aktuell(self, pj):
        try:
            return Ticket_Empfängerfirma_Aktuell.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = self).latest('zeitstempel').aktuell
        except ObjectDoesNotExist:
            return None

    # TICKET_EMPFÄNGERFIRMA GELESEN
    def _gelesen(self, pj):
        qs_gel = Ticket_Empfängerfirma_Gelesen.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = self)
        if qs_gel:
            return True
        else:
            return False

    # TICKET_EMPFÄNGERFIRMA STATUS
    def _status(self, pj):
        ti_empf = Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = self).latest('zeitstempel')
        return ti_empf.status.bezeichnung

class Ticket_Empfängerfirma_Aktuell(models.Model):
    ticket_empfängerfirma = models.ForeignKey(Ticket_Empfängerfirma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = timezone.now()

class Ticket_Empfängerfirma_Gelesen(models.Model):
    ticket_empfängerfirma = models.ForeignKey(Ticket_Empfängerfirma, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Empfängerfirma_Status(models.Model):
    ticket_empfängerfirma = models.ForeignKey(Ticket_Empfängerfirma, on_delete = models.CASCADE)
    status = models.ForeignKey(Status, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Kommentar(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    mitarbeiter_id = models.CharField(max_length = 20)
    text = models.CharField(max_length = 250)
    zeitstempel = models.DateTimeField()

class Plan(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    breite = models.FloatField()
    hoehe = models.FloatField()
    datei = models.ForeignKey(Datei, on_delete = models.CASCADE)

class Ticket_Plan(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Plan_X(models.Model):
    ticket_plan = models.ForeignKey(Ticket_Plan, on_delete = models.CASCADE)
    x_koordinate = models.FloatField()
    zeitstempel = models.DateTimeField()

class Ticket_Plan_Y(models.Model):
    ticket_plan = models.ForeignKey(Ticket_Plan, on_delete = models.CASCADE)
    y_koordinate = models.FloatField()
    zeitstempel = models.DateTimeField()

class Pfad_Plaene(models.Model):
    pfad = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()

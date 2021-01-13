from django.db import models
from django.contrib.auth.models import AbstractUser

class Firma(models.Model):
    bezeichnung = models.CharField(max_length=50)
    kurzbezeichnung = models.CharField(max_length=10)
    strasse = models.CharField(max_length=50, null=True)
    hausnummer = models.CharField(max_length=50, null=True)
    postleitzahl = models.IntegerField()
    ort = models.CharField(max_length=50)
    email_office = models.EmailField()
    email = models.EmailField()

    def __str__(self):
        return self.kurzbezeichnung

class Mitarbeiter(AbstractUser):
    firma = models.ForeignKey(
        'Firma', 
        on_delete=models.CASCADE,
        null = True)
    ist_firmenadmin = models.BooleanField(default = False)
    ist_superadmin = models.BooleanField(default = False)

    def __str__(self):
        return self.username

class Projekt(models.Model):
    bezeichnung = models.CharField(max_length=50)
    kurzbezeichnung = models.CharField(max_length=10)
    mitarbeiter = models.ManyToManyField(
        'Mitarbeiter',
        through = 'Projekt_Mitarbeiter_Mail',
        through_fields = ('projekt', 'mitarbeiter'),
    )
    firma = models.ManyToManyField(
        Firma,
        through = 'Projekt_Firma_Mail',
        through_fields = ('projekt', 'firma'),
    )

    def __str__(self):
        return self.kurzbezeichnung

class Projekt_Mitarbeiter_Mail(models.Model):
    ist_projektadmin = models.BooleanField()
    email = models.EmailField()
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    mitarbeiter = models.ForeignKey('Mitarbeiter', on_delete = models.CASCADE)

    def __str__(self):
        return str('%s - %s, %s' % (self.projekt.kurzbezeichnung, self.mitarbeiter.last_name, self.mitarbeiter.first_name,))

class Projekt_Firma_Mail(models.Model):
    ist_projektadmin = models.BooleanField()
    email = models.EmailField()
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    firma = models.ForeignKey('Firma', on_delete = models.CASCADE)

    def __str__(self):
        return str(self.projekt.kurzbezeichnung + '-' + self.firma.kurzbezeichnung)
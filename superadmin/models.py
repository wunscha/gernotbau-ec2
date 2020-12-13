from django.db import models
from django.contrib.auth.models import AbstractUser

class Firma(models.Model):
    bezeichnung = models.CharField(max_length=50)
    kurzbezeichnung = models.CharField(max_length=10)
    adresse = models.CharField(max_length=50)
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

    def __str__(self):
        return self.username

# Create your models here.

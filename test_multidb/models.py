from django.db import models

class TEST_Dokument(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    zeit_erstellung = models.DateTimeField(auto_now_add = True)
    mitarbeiter_id = models.IntegerField()

    def __str__(self):
        return self.bezeichnung
from django.db import models

class KeyWord(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Enrichment(models.Model):
    name = models.CharField( max_length=255, unique=True)
    keywords = models.ManyToManyField(KeyWord, blank=True)
    photo = models.ImageField(upload_to='enrichments/', default="")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

from wsgiref.validate import validator
from django.db import models
from django.core.validators import validate_image_file_extension
import os

class KeyWord(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Enrichment(models.Model):
    name = models.CharField( max_length=255, unique=True)
    keywords = models.ManyToManyField(KeyWord, blank=True)
    # validate given an image with thanks to https://stackoverflow.com/a/63705082/3023411
    photo = models.ImageField(upload_to='enrichments/', default="", validators=[validate_image_file_extension])

    class Meta:
        ordering = ['name']

    def photo_file_name(self):
        return os.path.basename(self.photo.name)

    def __str__(self):
        return self.name

from django.db import models
from django.core.validators import validate_image_file_extension
import os
from PIL import Image 

class Enrichment(models.Model):
    name = models.CharField( max_length=255, unique=True)
    # validate given an image with thanks to https://stackoverflow.com/a/63705082/3023411
    photo = models.ImageField(upload_to='enrichments/', default="", validators=[validate_image_file_extension])
    # string FK so ents doesn't have to import the zoo app (which itself imports Enrichment)
    category = models.ForeignKey('zoo.ItemCategory', on_delete=models.SET_NULL, null=True, blank=True)
    is_food = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def photo_file_name(self):
        return os.path.basename(self.photo.name)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.photo:
            return
        img=Image.open(self.photo)
        if img.height > 960 or img.width >540:
            Max_size=(540,960)
            img.thumbnail(Max_size)
            img.save(self.photo.path)
        else:
            del img

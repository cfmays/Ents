from django.db import models
from django.core.validators import validate_image_file_extension
import os
from PIL import Image 

def join_comments(*texts):
    """Join comments with ' | ', skipping blanks and repeats."""
    parts = []
    for text in texts:
        for part in text.split(' | '):
            part = part.strip()
            if part and part not in parts:
                parts.append(part)
    return ' | '.join(parts)


def combined_items_notice(items):
    """A warning naming any combined items among `items`, or '' if there are none."""
    names = [item.name for item in items if item.components.exists()]
    if not names:
        return ''
    if len(names) == 1:
        return f'{names[0]} is a combined item, and a combined item cannot be a component of another item.'
    return f'{", ".join(names)} are combined items, and a combined item cannot be a component of another item.'


class Enrichment(models.Model):
    name = models.CharField( max_length=255, unique=True)
    # validate given an image with thanks to https://stackoverflow.com/a/63705082/3023411
    photo = models.ImageField(upload_to='enrichments/', default="", blank=True, validators=[validate_image_file_extension])
    # string FK so ents doesn't have to import the zoo app (which itself imports Enrichment)
    category = models.ForeignKey('zoo.ItemCategory', on_delete=models.SET_NULL, null=True, blank=True)
    is_food = models.BooleanField(default=False)
    # shown on every calendar the item is on, before that calendar's own comment
    comments = models.CharField(max_length=500, blank=True)
    # items that interact and are used together as one enrichment (blank for a normal single item)
    components = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='used_in')

    class Meta:
        ordering = ['name']

    def photo_file_name(self):
        return os.path.basename(self.photo.name)

    def __str__(self):
        return self.name

    def component_comments(self):
        """The item comments of a combined item's components (always their current text)."""
        return join_comments(*[c.comments for c in self.components.all()])

    def all_comments(self):
        """This item's own comment, then its components' item comments."""
        return join_comments(self.comments, self.component_comments())

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

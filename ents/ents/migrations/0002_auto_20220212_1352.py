# Generated by Django 3.2.9 on 2022-02-12 13:52

from django.db import migrations

def seed_keywords(apps, schema_editor):
    KeyWord = apps.get_model('ents', 'KeyWord')
    KeyWord.objects.update_or_create(name="ball")
    KeyWord.objects.update_or_create(name="feeder")




class Migration(migrations.Migration):

    dependencies = [
        ('ents', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_keywords),
    ]

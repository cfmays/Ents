import django.db.models.deletion
from django.db import migrations, models


def delete_old_asgs(apps, schema_editor):
    """Old per-individual ASGs were never real calendars; drop them (and their test approved items)."""
    ASG = apps.get_model('zoo', 'ASG')
    CalendarEntry = apps.get_model('zoo', 'CalendarEntry')
    if CalendarEntry.objects.exists():
        raise RuntimeError('Calendar entries exist; refusing to delete old ASGs.')
    print(f"\n  Deleting {ASG.objects.count()} old ASGs")
    ASG.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('zoo', '0008_move_asgs_to_training_animals'),
    ]

    operations = [
        migrations.RemoveField(model_name='asg', name='maintenance_behaviors'),
        migrations.RemoveField(model_name='asg', name='new_behaviors'),
        migrations.RemoveField(model_name='asg', name='reinforcers'),
        migrations.RemoveField(model_name='trainingsession', name='asg'),
        migrations.RunPython(delete_old_asgs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='trainingsession',
            name='animal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_sessions', to='zoo.traininganimal'),
        ),
    ]

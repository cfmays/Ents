from django.db import migrations


def asgs_to_training_animals(apps, schema_editor):
    ASG = apps.get_model('zoo', 'ASG')
    TrainingAnimal = apps.get_model('zoo', 'TrainingAnimal')
    TrainingSession = apps.get_model('zoo', 'TrainingSession')
    CalendarEntry = apps.get_model('zoo', 'CalendarEntry')

    print(f"\n  Before: {ASG.objects.count()} ASGs, {CalendarEntry.objects.count()} calendar entries, "
          f"{TrainingSession.objects.count()} training sessions")

    for asg in ASG.objects.all():
        animal = TrainingAnimal.objects.create(name=asg.name, string=asg.string, notes=asg.notes)
        animal.maintenance_behaviors.set(asg.maintenance_behaviors.all())
        animal.new_behaviors.set(asg.new_behaviors.all())
        animal.reinforcers.set(asg.reinforcers.all())
        TrainingSession.objects.filter(asg=asg).update(animal=animal)

    print(f"  After: {TrainingAnimal.objects.count()} training animals, "
          f"{TrainingSession.objects.filter(animal__isnull=False).count()} sessions repointed")


class Migration(migrations.Migration):

    dependencies = [
        ('zoo', '0007_traininganimal'),
    ]

    operations = [
        migrations.RunPython(asgs_to_training_animals, migrations.RunPython.noop),
    ]

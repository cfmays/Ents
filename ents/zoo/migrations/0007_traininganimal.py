import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoo', '0006_alter_animal_options_alter_asg_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingAnimal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('notes', models.TextField(blank=True)),
                ('maintenance_behaviors', models.ManyToManyField(blank=True, limit_choices_to={'behavior_type': 'maintenance'}, related_name='training_animals_maintenance', to='zoo.behavior')),
                ('new_behaviors', models.ManyToManyField(blank=True, limit_choices_to={'behavior_type': 'new'}, related_name='training_animals_new', to='zoo.behavior')),
                ('reinforcers', models.ManyToManyField(blank=True, related_name='training_animals', to='zoo.reinforcer')),
                ('string', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='training_animals', to='zoo.string')),
            ],
            options={
                'verbose_name': 'training animal',
                'verbose_name_plural': 'training animals',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='trainingsession',
            name='animal',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='training_sessions_new', to='zoo.traininganimal'),
        ),
    ]

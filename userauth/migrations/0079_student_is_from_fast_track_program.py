# Generated by Django 3.2 on 2023-02-02 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0078_alter_studentschooldetail_school_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='is_from_fast_track_program',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]

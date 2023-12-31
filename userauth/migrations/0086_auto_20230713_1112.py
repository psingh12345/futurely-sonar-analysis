# Generated by Django 3.2 on 2023-07-13 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0085_person_clarity_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='counselor',
            name='is_for_fast_track_program_only',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='counselor',
            name='is_for_middle_school_only',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]

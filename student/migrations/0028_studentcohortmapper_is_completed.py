# Generated by Django 3.2 on 2022-02-17 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0027_auto_20211215_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentcohortmapper',
            name='is_completed',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]

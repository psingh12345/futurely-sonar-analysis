# Generated by Django 3.2 on 2023-01-05 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0061_studentactionitemtypetable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentactionitemtypetable',
            name='answer',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

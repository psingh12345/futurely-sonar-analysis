# Generated by Django 3.2 on 2023-07-04 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unipegaso', '0008_alter_studentdetail_certificate_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentdetail',
            name='clarity_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

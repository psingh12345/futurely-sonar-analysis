# Generated by Django 3.2 on 2023-03-13 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0072_certificatedownload'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificatedownload',
            name='download_count',
        ),
    ]

# Generated by Django 3.2 on 2021-07-26 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0028_personnotification'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionitemfiles',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='actionitemlinks',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]

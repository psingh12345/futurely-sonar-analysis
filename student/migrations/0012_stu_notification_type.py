# Generated by Django 3.2 on 2021-08-03 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_personnotification'),
    ]

    operations = [
        migrations.AddField(
            model_name='stu_notification',
            name='type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

# Generated by Django 3.2 on 2022-11-11 05:23

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0067_merge_20220830_1145'),
    ]

    operations = [
        migrations.AddField(
            model_name='counselor',
            name='academic_section',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]

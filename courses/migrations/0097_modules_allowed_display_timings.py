# Generated by Django 3.2 on 2023-02-13 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0096_mypdfs_is_for_middle_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='modules',
            name='allowed_display_timings',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]

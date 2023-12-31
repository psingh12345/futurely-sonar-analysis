# Generated by Django 3.2 on 2023-08-23 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0088_alter_counselor_is_trial_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='attempts',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='person',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
    ]

# Generated by Django 3.2 on 2022-01-28 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0057_ourplans_weekly_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='ourplans',
            name='weekly_cost_duration',
            field=models.IntegerField(blank=True, default=10, null=True),
        ),
    ]

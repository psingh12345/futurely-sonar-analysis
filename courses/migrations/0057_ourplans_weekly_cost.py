# Generated by Django 3.2 on 2022-01-28 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0056_auto_20211215_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='ourplans',
            name='weekly_cost',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]

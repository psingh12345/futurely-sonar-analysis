# Generated by Django 3.2 on 2021-08-30 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0037_auto_20210826_0600'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='src',
            field=models.CharField(blank=True, default='general', max_length=50),
        ),
    ]

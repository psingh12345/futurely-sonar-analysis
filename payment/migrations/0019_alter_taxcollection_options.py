# Generated by Django 3.2 on 2021-11-03 21:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0018_auto_20211103_1526'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taxcollection',
            options={'verbose_name': 'TaxCollection', 'verbose_name_plural': 'TaxCollections'},
        ),
    ]

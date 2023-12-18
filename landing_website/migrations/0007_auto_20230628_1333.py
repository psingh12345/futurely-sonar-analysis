# Generated by Django 3.2 on 2023-06-28 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landing_website', '0006_auto_20230628_1206'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contactus',
            options={'verbose_name': 'ContactUs', 'verbose_name_plural': 'ContactUs'},
        ),
        migrations.AlterField(
            model_name='contactus',
            name='organization',
            field=models.CharField(choices=[('Scuola', 'Scuola'), ('Università', 'Università'), ('Azienda', 'Azienda'), ('Altro', 'Altro')], max_length=100),
        ),
    ]

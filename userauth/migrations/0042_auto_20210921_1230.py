# Generated by Django 3.2 on 2021-09-21 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0041_auto_20210914_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='contact_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='how_know_us',
            field=models.CharField(blank=True, choices=[('Facebook', 'Facebook'), ('Instagram', 'Instagram'), ('Tik Tok', 'Tik Tok'), ('Google', 'Google'), ('Friends', 'Friends'), ('Parents', 'Parents'), ('School', 'School'), ('Radio', 'Radio'), ('News Paper', 'News Paper'), ('Linkedin', 'Linkedin'), ('Other', 'Other')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='how_know_us_other',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

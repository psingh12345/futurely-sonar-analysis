# Generated by Django 3.2 on 2021-08-23 01:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0012_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentschooldetail',
            name='class_name',
            field=models.CharField(choices=[('Select Class Name', 'Select Class Name'), ('A Class', 'A Class'), ('B Class', 'B Class')], default='', max_length=70),
        ),
        migrations.AddField(
            model_name='studentschooldetail',
            name='class_year',
            field=models.CharField(choices=[('Select Class Year', 'Select Class Year'), ('1st Year', '1st Year'), ('2nd Year', '2nd Year'), ('3rd Year', '3rd Year'), ('4th Year', '4th Year'), ('5th Year', '5th Year')], default='', max_length=70),
        ),
        migrations.AddField(
            model_name='studentschooldetail',
            name='specialization',
            field=models.CharField(choices=[('Select Specialization', 'Select Specialization'), ('X', 'X'), ('Y', 'Y')], default='', max_length=70),
        ),
    ]

# Generated by Django 3.2 on 2021-08-25 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0017_auto_20210825_0800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='are_you_a_student',
            field=models.CharField(choices=[(None, 'Are you a student?'), ('Yes', 'Yes'), ('No', 'No')], default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='student',
            name='are_you_from_futurelabs',
            field=models.CharField(blank=True, choices=[('Are you enrolling from a future lab session?', 'Are you enrolling from a future lab session?'), ('Yes', 'Yes'), ('No', 'No')], max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='are_you_part_of_company_welfare_program',
            field=models.CharField(blank=True, choices=[('Are you part of a company welfare program?', 'Are you part of a company welfare program?'), ('Yes', 'Yes'), ('No', 'No')], max_length=70, null=True),
        ),
    ]

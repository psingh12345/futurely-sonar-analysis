# Generated by Django 3.2 on 2021-11-10 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0049_futurelyadmin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='are_you_a_student',
            field=models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='Yes', max_length=30, null=True),
        ),
    ]

# Generated by Django 3.2 on 2022-11-11 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0069_rename_academic_section_counselor_academic_session_start_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='counselor',
            name='academic_session_start_date',
            field=models.DateField(default='2022-08-01'),
        ),
    ]

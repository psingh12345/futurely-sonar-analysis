# Generated by Django 3.2 on 2023-02-17 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0067_studentactionitemtypetablestep8'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentpctorecord',
            name='pcto_hour_source',
            field=models.CharField(blank=True, choices=[('Future-lab', 'Future-lab'), ('Webinar', 'Webinar'), ('Course-1', 'Course-1'), ('Course-2', 'Course-2')], default='Webinar', max_length=50),
        ),
    ]

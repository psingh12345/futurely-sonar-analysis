# Generated by Django 3.2 on 2023-09-27 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0095_auto_20230927_0915'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='companywithschooldetail',
            name='school',
        ),
        migrations.AddField(
            model_name='school',
            name='company_path_type',
            field=models.CharField(blank=True, choices=[('BOTH', 'BOTH'), ('Middle School', 'Middle School'), ('High School', 'High School')], default='', max_length=50, null=True),
        ),
    ]

# Generated by Django 3.2 on 2023-01-23 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0077_alter_studentparentsdetail_parent_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentschooldetail',
            name='school_type',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]

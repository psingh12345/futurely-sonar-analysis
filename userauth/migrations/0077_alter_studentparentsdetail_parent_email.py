# Generated by Django 3.2 on 2023-01-12 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0076_alter_studentparentsdetail_parent_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentparentsdetail',
            name='parent_email',
            field=models.CharField(default='', max_length=100),
        ),
    ]

# Generated by Django 3.2 on 2021-08-25 13:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0030_classname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentschooldetail',
            name='class_name',
        ),
        migrations.RemoveField(
            model_name='studentschooldetail',
            name='class_year',
        ),
        migrations.RemoveField(
            model_name='studentschooldetail',
            name='specialization',
        ),
        migrations.AlterField(
            model_name='student',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='students', to='userauth.company'),
        ),
    ]

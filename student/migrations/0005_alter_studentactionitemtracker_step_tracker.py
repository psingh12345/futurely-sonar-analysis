# Generated by Django 3.2 on 2021-07-14 13:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_auto_20210707_0608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentactionitemtracker',
            name='step_tracker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stu_action_items', to='student.cohortsteptracker'),
        ),
    ]

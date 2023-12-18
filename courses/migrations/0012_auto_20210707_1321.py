# Generated by Django 3.2 on 2021-07-07 13:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0011_auto_20210707_0608'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cohort',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='step_status',
            name='is_active',
        ),
        migrations.AlterField(
            model_name='step_status',
            name='cohort',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cohort_step_status', to='courses.cohort'),
        ),
        migrations.AlterField(
            model_name='steps',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='courses.modules'),
        ),
    ]

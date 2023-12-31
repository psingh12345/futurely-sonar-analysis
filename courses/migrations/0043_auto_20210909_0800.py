# Generated by Django 3.2 on 2021-09-09 08:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0042_auto_20210908_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stu_notifications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='notification',
            name='cohort',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='courses.cohort'),
        ),
    ]

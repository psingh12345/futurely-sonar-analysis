# Generated by Django 3.2 on 2021-09-21 22:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('web_analytics', '0011_alter_customevent_event_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customevent',
            name='person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='events', to=settings.AUTH_USER_MODEL),
        ),
    ]

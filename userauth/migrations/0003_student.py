# Generated by Django 3.2 on 2021-06-02 13:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0002_auto_20210601_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('school_class', models.CharField(max_length=30, verbose_name='Class')),
                ('school_region', models.CharField(max_length=30)),
                ('school_city', models.CharField(max_length=30)),
                ('school_name', models.CharField(max_length=30)),
                ('school_type', models.CharField(max_length=30)),
                ('person', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

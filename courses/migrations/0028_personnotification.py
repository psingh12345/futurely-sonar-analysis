# Generated by Django 3.2 on 2021-07-25 07:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0027_notification_type_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('notification_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='person_notifications', to='courses.notification_type')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='person_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'PersonNotification',
                'verbose_name_plural': 'PersonNotifications',
            },
        ),
    ]

# Generated by Django 3.2 on 2021-10-08 15:46

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0046_alter_ourplans_plan_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeetupCommunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('title', models.CharField(max_length=100)),
                ('meet_link', models.URLField()),
                ('meet_day', models.CharField(choices=[('1', 'Monday'), ('2', 'Tuesday'), ('3', 'Wednesday'), ('4', 'Thursday'), ('5', 'Friday'), ('6', 'Saturday'), ('7', 'Sunday')], max_length=100)),
                ('meet_time', models.TimeField(default=django.utils.timezone.now)),
                ('meet_tutor_name', models.CharField(max_length=100)),
                ('is_Active', models.BooleanField(default=False)),
                ('meet_app', models.CharField(choices=[('Zoom', 'Zoom')], default='Zoom', max_length=20)),
            ],
            options={
                'verbose_name': 'MeetupCommunity',
                'verbose_name_plural': 'MeetupCommunity',
            },
        ),
        migrations.CreateModel(
            name='Meetup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('title', models.CharField(max_length=100)),
                ('meet_link', models.URLField()),
                ('meet_date_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('meet_tutor_name', models.CharField(max_length=100)),
                ('is_Active', models.BooleanField(default=False)),
                ('meet_app', models.CharField(choices=[('Zoom', 'Zoom')], default='Zoom', max_length=20)),
                ('cohort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meetups', to='courses.cohort')),
            ],
            options={
                'verbose_name': 'Meetup',
                'verbose_name_plural': 'Meetups',
            },
        ),
    ]

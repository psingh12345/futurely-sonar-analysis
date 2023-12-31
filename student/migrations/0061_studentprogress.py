# Generated by Django 3.2 on 2023-01-05 06:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0075_merge_20221216_0853'),
        ('student', '0060_auto_20221209_1137'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('endurance_score', models.CharField(blank=True, default='0', max_length=20)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_endurance_score', to='userauth.student')),
            ],
            options={
                'verbose_name': 'StudentProgress',
                'verbose_name_plural': 'StudentsProgress',
            },
        ),
    ]

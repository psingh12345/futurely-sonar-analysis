# Generated by Django 3.2 on 2022-11-27 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0070_alter_counselor_academic_session_start_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='is_welcome_video_played',
            field=models.BooleanField(default=False),
        ),
    ]

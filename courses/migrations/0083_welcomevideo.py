# Generated by Django 3.2 on 2022-11-27 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0082_auto_20221117_0454'),
    ]

    operations = [
        migrations.CreateModel(
            name='WelcomeVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('video_title', models.CharField(blank=True, max_length=70)),
                ('video_link', models.URLField()),
                ('video_description', models.TextField(blank=True, default='')),
                ('front_pic', models.FileField(blank=True, upload_to='images')),
                ('module_lang', models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20)),
                ('is_published', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'WelcomeVideo',
                'verbose_name_plural': 'WelcomeVideos',
            },
        ),
    ]

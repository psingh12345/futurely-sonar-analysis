# Generated by Django 3.2 on 2023-05-07 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0106_auto_20230506_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionitemfiles',
            name='file_box_link',
            field=models.URLField(blank=True, null=True),
        ),
    ]

# Generated by Django 3.2 on 2023-06-07 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0079_studentactionitemdiarycomment_comments_total_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentactionitemdiarycomment',
            name='comments_total_count',
        ),
        migrations.AddField(
            model_name='cohortsteptrackerdetails',
            name='total_comments',
            field=models.IntegerField(default=0),
        ),
    ]

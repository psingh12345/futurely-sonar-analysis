# Generated by Django 3.2 on 2023-07-08 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0109_alter_actionitemframework_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='actionitemdiary',
            name='is_linked_with_ai_comment',
            field=models.BooleanField(default=False),
        ),
    ]

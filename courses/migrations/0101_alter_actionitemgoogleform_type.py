# Generated by Django 3.2 on 2023-03-13 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0100_auto_20230223_1104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionitemgoogleform',
            name='type',
            field=models.CharField(blank=True, choices=[('MCQ', 'MCQ'), ('Rating', 'Rating'), ('Star', 'Star'), ('Dropdown', 'Dropdown'), ('Text', 'Text'), ('Other', 'Other')], default='Other', max_length=200, null=True),
        ),
    ]

# Generated by Django 3.2 on 2022-08-04 16:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0069_auto_20220804_1427'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='webinars',
            options={'ordering': ('webinar_start_date',), 'verbose_name': 'Webinars', 'verbose_name_plural': 'Webinars'},
        ),
        migrations.RenameField(
            model_name='webinars',
            old_name='publish_date',
            new_name='webinar_start_date',
        ),
    ]

# Generated by Django 3.2 on 2021-09-08 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0040_auto_20210902_0828'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actionitems',
            options={'ordering': ('action_sno',), 'verbose_name': 'ActionItem', 'verbose_name_plural': 'ActionItems'},
        ),
        migrations.AddField(
            model_name='actionitems',
            name='action_sno',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]

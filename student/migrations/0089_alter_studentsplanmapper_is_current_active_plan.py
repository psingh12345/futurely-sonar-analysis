# Generated by Django 3.2 on 2023-07-11 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0088_merge_0081_auto_20230706_0518_0087_auto_20230708_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentsplanmapper',
            name='is_current_active_plan',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]

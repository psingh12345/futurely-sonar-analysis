# Generated by Django 3.2 on 2021-07-06 11:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_auto_20210706_1109'),
        ('student', '0002_auto_20210706_1123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentactionitemdairy',
            name='action_item_dairy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stu_action_item_dairy', to='courses.actionitemdairy'),
        ),
    ]

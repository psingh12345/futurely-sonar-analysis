# Generated by Django 3.2 on 2021-07-15 10:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0015_auto_20210715_0721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionitemfiles',
            name='action_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='courses.actionitems'),
        ),
    ]

# Generated by Django 3.2 on 2023-10-17 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0115_alter_ourplans_plan_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='myblogvideos',
            name='sno',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

# Generated by Django 3.2 on 2021-08-09 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0003_coupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='discount_value',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

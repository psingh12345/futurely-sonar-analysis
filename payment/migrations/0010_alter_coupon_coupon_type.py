# Generated by Django 3.2 on 2021-08-23 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0009_auto_20210812_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='coupon_type',
            field=models.CharField(choices=[('FutureLab', 'FutureLab'), ('Organization', 'Organization'), ('General', 'General')], default='General', max_length=50),
        ),
    ]

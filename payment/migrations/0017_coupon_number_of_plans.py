# Generated by Django 3.2 on 2021-10-16 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0016_alter_payment_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='number_of_plans',
            field=models.CharField(choices=[('2', '2'), ('3', '3')], default='3', max_length=10),
        ),
    ]

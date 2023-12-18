# Generated by Django 3.2 on 2021-09-03 04:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0012_auto_20210902_1236'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='program_type',
        ),
        migrations.AddField(
            model_name='coupon',
            name='plan_type',
            field=models.CharField(choices=[('Elite', 'Elite'), ('Premium', 'Premium'), ('Master', 'Master')], default='Premium', max_length=30),
        ),
    ]

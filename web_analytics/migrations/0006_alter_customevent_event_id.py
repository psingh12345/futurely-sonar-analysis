# Generated by Django 3.2 on 2021-08-09 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_analytics', '0005_auto_20210809_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customevent',
            name='event_id',
            field=models.CharField(choices=[(1, 'Sign up - Stage 1'), (2, 'Sign up - Stage 2'), (3, 'Login - Success'), (4, 'Login - Fail'), (5, 'Payment - Success'), (6, 'Payment - Fail'), (7, 'Home'), (8, 'Students'), (9, 'High Schools'), (10, 'About us'), (11, 'dashboard'), (12, '404'), (13, 'Course 1 purchase'), (14, 'Course 1 and 2 purchase')], max_length=50),
        ),
    ]

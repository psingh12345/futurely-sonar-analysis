# Generated by Django 3.2 on 2021-08-02 10:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_analytics', '0003_auto_20210802_0942'),
    ]

    operations = [
        migrations.AddField(
            model_name='customevent',
            name='event_id',
            field=models.CharField(choices=[(1, 'Sign up - Stage 1'), (2, 'Sign up - Stage 2'), (3, 'Login - Success'), (4, 'Login - Fail'), (5, 'Payment - Success'), (6, 'Payment - Fail')], default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customevent',
            name='event_name',
            field=models.CharField(max_length=50),
        ),
    ]

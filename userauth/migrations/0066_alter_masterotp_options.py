# Generated by Django 3.2 on 2022-07-28 07:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0065_merge_0064_masterotp_0064_student_total_pcto_hours'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='masterotp',
            options={'verbose_name': 'MasterOTP', 'verbose_name_plural': 'MasterOTPS'},
        ),
    ]

# Generated by Django 3.2 on 2022-07-26 12:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0063_studentparentsdetail'),
    ]

    operations = [
        migrations.CreateModel(
            name='MasterOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('otp', models.CharField(max_length=30)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

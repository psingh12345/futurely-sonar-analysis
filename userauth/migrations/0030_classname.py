# Generated by Django 3.2 on 2021-08-25 13:32

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0029_auto_20210825_1330'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassName',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('name', models.CharField(max_length=200)),
                ('country', models.CharField(choices=[('USA', 'USA'), ('Italy', 'Italy')], default='Italy', max_length=70)),
            ],
            options={
                'verbose_name': 'ClassName',
                'verbose_name_plural': 'ClassNames',
            },
        ),
    ]

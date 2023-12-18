# Generated by Django 3.2 on 2023-06-28 08:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0082_counselorwithspecialdashboard'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='classname',
            options={'ordering': ['name_sno'], 'verbose_name': 'ClassName', 'verbose_name_plural': 'ClassNames'},
        ),
        migrations.AlterModelOptions(
            name='classyear',
            options={'ordering': ['year_sno'], 'verbose_name': 'ClassYear', 'verbose_name_plural': 'ClassYears'},
        ),
        migrations.AddField(
            model_name='classname',
            name='name_sno',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='classyear',
            name='year_sno',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='counselorwithspecialdashboard',
            name='counselor',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='userauth.counselor'),
        ),
    ]

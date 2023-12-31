# Generated by Django 3.2 on 2021-09-01 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0038_auto_20210829_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='cohort',
            name='cohort_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='blog_post',
            name='module_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='modules',
            name='module_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='myblogvideos',
            name='module_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='myresources',
            name='module_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='myvideos',
            name='module_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='ourplans',
            name='plan_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
        migrations.AlterField(
            model_name='webinars',
            name='module_lang',
            field=models.CharField(blank=True, choices=[('en-us', 'English'), ('it', 'Italiano')], default='it', max_length=20),
        ),
    ]

# Generated by Django 3.2 on 2022-07-21 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0031_studentpersonalitytestmapper_lang_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScholarshipTestQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('question', models.CharField(blank=True, max_length=250, null=True)),
                ('sno', models.IntegerField(blank=True, default=1, null=True)),
            ],
            options={
                'verbose_name': 'ScholarshipTestQuestion',
                'verbose_name_plural': 'ScholarshipTestQuestions',
            },
        ),
    ]

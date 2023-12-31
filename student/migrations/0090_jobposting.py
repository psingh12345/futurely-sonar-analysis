# Generated by Django 3.2 on 2023-11-09 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0089_alter_studentsplanmapper_is_current_active_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobPosting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('company_name', models.CharField(max_length=255)),
                ('company_logo', models.ImageField(upload_to='company_logos/')),
                ('location', models.CharField(max_length=255)),
                ('job_portal_link', models.URLField()),
                ('start_date', models.DateField(auto_now_add=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'JobPosting',
                'verbose_name_plural': 'JobPostings',
            },
        ),
    ]

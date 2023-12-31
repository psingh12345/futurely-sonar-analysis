# Generated by Django 3.2 on 2022-01-05 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0056_auto_20211215_0647'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('template_name', models.CharField(max_length=100)),
                ('template_file', models.FileField(upload_to='email_template')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

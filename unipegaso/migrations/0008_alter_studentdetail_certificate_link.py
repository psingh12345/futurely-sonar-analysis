# Generated by Django 3.2 on 2023-04-26 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unipegaso', '0007_alter_studentdetail_certificate_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentdetail',
            name='certificate_link',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]

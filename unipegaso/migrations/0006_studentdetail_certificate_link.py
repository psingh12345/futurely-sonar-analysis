# Generated by Django 3.2 on 2023-04-26 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unipegaso', '0005_approvedcentreoption_option_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentdetail',
            name='certificate_link',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]

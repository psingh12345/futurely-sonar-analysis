# Generated by Django 3.2 on 2023-06-29 05:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('landing_website', '0008_alter_contactus_organization_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contactus',
            old_name='organization_name',
            new_name='organization_name_other',
        ),
    ]

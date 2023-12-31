# Generated by Django 3.2 on 2023-09-13 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0091_counselor_course_module'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='accept_data_third_party',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='student',
            name='accept_marketing',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='student',
            name='accept_tracking',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='student',
            name='privacy_policy_mandatory',
            field=models.BooleanField(default=False),
        ),
    ]

# Generated by Django 3.2 on 2023-11-30 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0118_jobposting_company_to_display_specific_jobs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionitemexitticket',
            name='type',
            field=models.CharField(blank=True, choices=[('MCQ', 'MCQ'), ('Rating', 'Rating'), ('Checkbox', 'Checkbox'), ('Dropdown', 'Dropdown'), ('Text', 'Text'), ('Other', 'Other')], default='Other', max_length=200, null=True),
        ),
    ]

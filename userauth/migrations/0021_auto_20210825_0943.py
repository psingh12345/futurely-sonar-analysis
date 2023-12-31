# Generated by Django 3.2 on 2021-08-25 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0020_alter_student_are_you_from_futurelabs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='are_you_a_student',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='student',
            name='are_you_fourteen_plus',
            field=models.CharField(choices=[('Yes', 'Yes'), ('No', 'No')], default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='student',
            name='are_you_from_futurelabs',
            field=models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='are_you_part_of_company_welfare_program',
            field=models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], max_length=70, null=True),
        ),
    ]

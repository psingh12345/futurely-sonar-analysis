# Generated by Django 3.2 on 2023-12-12 15:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0102_student_stu_sponsor_compnay'),
    ]

    operations = [
        migrations.RenameField(
            model_name='student',
            old_name='stu_sponsor_compnay',
            new_name='sponsor_compnay',
        ),
    ]

# Generated by Django 3.2 on 2022-08-04 10:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0042_auto_20220804_1005'),
        ('courses', '0066_webinars_seat_book_date'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ScholarshipTestQuestion',
        ),
    ]

# Generated by Django 3.2 on 2021-09-21 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_analytics', '0010_alter_customevent_event_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customevent',
            name='event_id',
            field=models.CharField(choices=[(1, 'Sign up - Stage 1 Success'), (2, 'Sign up - Stage 2 Success'), (3, 'Login - Success'), (4, 'Login - Fail'), (5, 'Payment - Success'), (6, 'Payment - Fail'), (7, 'Home'), (8, 'Students'), (9, 'High Schools'), (10, 'About us'), (11, 'dashboard'), (12, '404'), (13, 'Course 1 purchase'), (14, 'Course 1 and 2 purchase'), (15, 'Cohort Info'), (16, 'Student Query - Success'), (17, 'Student Query - Fail'), (18, 'Mentors'), (19, 'Plans'), (20, 'Sign up - Stage 1 Visited'), (21, 'Sign up - Stage 2 Visited')], max_length=50),
        ),
    ]

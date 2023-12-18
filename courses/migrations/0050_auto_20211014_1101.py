# Generated by Django 3.2 on 2021-10-14 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0049_alter_meetup_step_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetupcommunity',
            name='meet_week_number',
            field=models.IntegerField(blank=True, default=3, null=True),
        ),
        migrations.AlterField(
            model_name='meetupcommunity',
            name='meet_day',
            field=models.CharField(choices=[('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday')], max_length=100),
        ),
    ]

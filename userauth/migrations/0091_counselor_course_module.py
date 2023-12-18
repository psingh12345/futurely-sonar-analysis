# Generated by Django 3.2 on 2023-09-13 04:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0114_myblogvideos_duration'),
        ('userauth', '0090_auto_20230912_0925'),
    ]

    operations = [
        migrations.AddField(
            model_name='counselor',
            name='course_module',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='counselors', to='courses.modules'),
        ),
    ]

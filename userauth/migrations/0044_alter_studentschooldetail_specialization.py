# Generated by Django 3.2 on 2021-10-10 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0043_auto_20211010_1858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentschooldetail',
            name='specialization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='student_school_details', to='userauth.specialization'),
        ),
    ]

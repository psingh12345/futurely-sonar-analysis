# Generated by Django 3.2 on 2022-11-17 04:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0080_webinarquestion_webinarquestionnaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='webinarquestionnaire',
            name='webinar',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.webinars'),
        ),
        migrations.AlterField(
            model_name='webinarquestion',
            name='webinar_test',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webinar_test_question', to='courses.webinarquestionnaire'),
        ),
    ]

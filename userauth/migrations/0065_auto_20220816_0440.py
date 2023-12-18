# Generated by Django 3.2 on 2022-08-16 04:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0064_auto_20220812_1101'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='studentdeleterequest',
            options={'verbose_name': 'StudentDeleteRequest', 'verbose_name_plural': 'StudentsDeleteRequest'},
        ),
        migrations.AlterField(
            model_name='studentdeleterequest',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delete_students', to=settings.AUTH_USER_MODEL),
        ),
    ]

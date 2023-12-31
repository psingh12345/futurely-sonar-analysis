# Generated by Django 3.2 on 2021-11-08 11:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0048_rename_number_of_plans_student_number_of_offered_plans'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuturelyAdmin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('person', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='futurely_admins', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'FuturelyAdmin',
                'verbose_name_plural': 'FuturelyAdmins',
            },
        ),
    ]

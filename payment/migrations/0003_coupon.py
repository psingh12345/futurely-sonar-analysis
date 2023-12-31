# Generated by Django 3.2 on 2021-08-06 07:04

import django.core.validators
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0002_alter_paymentcohort_cohort'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('code', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=200, null=True)),
                ('coupon_type', models.CharField(choices=[('FutureLab', 'FutureLab'), ('General', 'General')], default='General', max_length=30)),
                ('discount_type', models.CharField(choices=[('Fixed', 'Fixed'), ('Percentage', 'Percentage')], default='Fixed', max_length=30)),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=False)),
                ('discount_value', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
            ],
            options={
                'verbose_name': 'Coupon',
                'verbose_name_plural': 'Coupons',
            },
        ),
    ]

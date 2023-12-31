# Generated by Django 3.2 on 2023-04-18 07:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0103_actionitemframework'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionItemConnectWithOtherActionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('ai_relation_type', models.CharField(blank=True, choices=[('AutoFill', 'AutoFill'), ('Other', 'Other')], default='AutoFill', max_length=50, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('primary_action_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primary_action_item', to='courses.actionitems')),
                ('secondary_action_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='secondary_action_item', to='courses.actionitemframework')),
            ],
            options={
                'verbose_name': 'ActionItemConnectWithOtherActionItem',
                'verbose_name_plural': 'ActionItemConnectWithOtherActionItems',
            },
        ),
    ]

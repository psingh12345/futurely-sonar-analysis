# Generated by Django 3.2 on 2023-01-29 14:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0093_actionitemtypetablestep8'),
        ('student', '0066_merge_20230109_1106'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentActionItemTypeTableStep8',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('rating_ans', models.IntegerField(blank=True, default=0, null=True)),
                ('comments_ans', models.TextField(blank=True, default='')),
                ('is_completed', models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No')], default='No', max_length=3)),
                ('action_item_track', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_item_type_table_step8_track', to='student.studentactionitemtracker')),
                ('action_item_type_table_step8', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stu_action_item_type_table_step8', to='courses.actionitemtypetablestep8')),
            ],
            options={
                'verbose_name': 'StudentActionItemTypeTableStep8',
                'verbose_name_plural': 'StudentActionItemTypeTableStep8',
                'ordering': ['action_item_type_table_step8__sno'],
            },
        ),
    ]

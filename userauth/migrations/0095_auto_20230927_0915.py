# Generated by Django 3.2 on 2023-09-27 09:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0094_auto_20230927_0642'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='companywithschooldetail',
            name='is_for_high_school',
        ),
        migrations.RemoveField(
            model_name='companywithschooldetail',
            name='is_for_middle_school',
        ),
        migrations.AddField(
            model_name='companywithschooldetail',
            name='company_path_type',
            field=models.CharField(blank=True, choices=[('BOTH', 'BOTH'), ('Middle School', 'Middle School'), ('High School', 'High School')], default='', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='companywithschooldetail',
            name='company',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='userauth.company'),
        ),
        migrations.RemoveField(
            model_name='companywithschooldetail',
            name='school',
        ),
        migrations.AddField(
            model_name='companywithschooldetail',
            name='school',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='userauth.school'),
            preserve_default=False,
        ),
    ]

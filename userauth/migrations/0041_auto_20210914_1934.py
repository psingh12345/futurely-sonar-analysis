# Generated by Django 3.2 on 2021-09-14 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0040_auto_20210914_1156'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='future_lab_form_link',
        ),
        migrations.AlterField(
            model_name='student',
            name='src',
            field=models.CharField(blank=True, choices=[('future_lab', 'future_lab'), ('company', 'company'), ('general', 'general')], default='general', max_length=50, verbose_name='Source'),
        ),
    ]

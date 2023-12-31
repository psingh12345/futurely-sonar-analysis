# Generated by Django 3.2 on 2023-07-14 10:34

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ifoa', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IFOANextQuestionOptionLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('video_link', models.CharField(max_length=200)),
                ('ifoa_next_question_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ifoa_next_qus_option_link', to='ifoa.ifoanextquestionmcqoption')),
            ],
            options={
                'verbose_name': 'IFOANextQuestionOptionLink',
                'verbose_name_plural': 'IFOANextQuestionOptionLinks',
            },
        ),
    ]

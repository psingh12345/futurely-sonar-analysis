# Generated by Django 3.2 on 2021-07-20 10:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('courses', '0021_blog_post_icon'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blog_post',
            options={'ordering': ('-publish_date',)},
        ),
        migrations.RenameField(
            model_name='blog_post',
            old_name='created',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='blog_post',
            old_name='updated',
            new_name='modified_at',
        ),
        migrations.RenameField(
            model_name='blog_post',
            old_name='publish',
            new_name='publish_date',
        ),
        migrations.AddField(
            model_name='blog_post',
            name='created_by',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='blog_post',
            name='modified_by',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.CreateModel(
            name='Webinars',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(blank=True, default='', max_length=150)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('modified_by', models.CharField(blank=True, default='', max_length=150)),
                ('title', models.CharField(max_length=250)),
                ('description', models.TextField()),
                ('link', models.URLField(blank=True, null=True)),
                ('publish_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('icon', models.FileField(blank=True, upload_to='images')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='draft', max_length=10)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webinars', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-publish_date',),
            },
        ),
    ]

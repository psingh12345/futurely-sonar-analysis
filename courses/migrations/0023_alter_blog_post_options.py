# Generated by Django 3.2 on 2021-07-20 15:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0022_auto_20210720_1037'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blog_post',
            options={'ordering': ('-publish_date',), 'verbose_name': 'Blog_post', 'verbose_name_plural': 'Blog_posts'},
        ),
    ]

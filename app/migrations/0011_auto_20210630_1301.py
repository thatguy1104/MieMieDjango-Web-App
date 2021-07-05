# Generated by Django 3.1.7 on 2021-06-30 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_userprofileact'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofileact',
            old_name='faculty',
            new_name='affiliation',
        ),
        migrations.RemoveField(
            model_name='userprofileact',
            name='email',
        ),
        migrations.AddField(
            model_name='userprofileact',
            name='author_id',
            field=models.CharField(default='', max_length=100, primary_key=True, serialize=False),
        ),
    ]
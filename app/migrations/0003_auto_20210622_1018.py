# Generated by Django 3.1.7 on 2021-06-22 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_approach_color_specialty_status_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='irisLink',
            field=models.URLField(default='', null=True),
        ),
    ]

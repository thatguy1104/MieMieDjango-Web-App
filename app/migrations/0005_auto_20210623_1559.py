# Generated by Django 3.1.7 on 2021-06-23 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_serializer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serializer',
            name='data',
            field=models.TextField(blank=True, null=True),
        ),
    ]

# Generated by Django 3.1.7 on 2021-06-16 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Department_Name', models.CharField(max_length=400)),
                ('Department_ID', models.CharField(max_length=200)),
                ('Module_Name', models.CharField(max_length=400)),
                ('Module_ID', models.CharField(max_length=200)),
                ('Faculty', models.CharField(max_length=400)),
                ('Credit_Value', models.IntegerField(blank=True, default=0, null=True)),
                ('Module_Lead', models.CharField(blank=True, max_length=200, null=True)),
                ('Catalogue_Link', models.CharField(max_length=400)),
                ('Description', models.TextField(blank=True, null=True)),
                ('assignedSDG', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=800)),
                ('data', models.JSONField(blank=True, null=True)),
                ('assignedSDG', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PyChart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100)),
                ('picture', models.ImageField(blank=True, default='', null=True, upload_to='charts/')),
            ],
        ),
    ]

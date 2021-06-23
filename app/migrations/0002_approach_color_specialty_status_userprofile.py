# Generated by Django 3.1.7 on 2021-06-21 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Approach',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Approach',
                'verbose_name_plural': 'Approaches',
            },
        ),
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Color',
                'verbose_name_plural': 'Colors',
            },
        ),
        migrations.CreateModel(
            name='Specialty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.color')),
            ],
            options={
                'verbose_name': 'Specialty',
                'verbose_name_plural': 'Specialties',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Status',
                'verbose_name_plural': 'Status',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('email', models.EmailField(max_length=254, primary_key=True, serialize=False)),
                ('fullName', models.CharField(default='', max_length=100)),
                ('irisLink', models.URLField(default='')),
                ('faculty', models.CharField(default='', max_length=200)),
                ('start_time', models.DateField(blank=True, null=True)),
                ('approach', models.ManyToManyField(blank=True, to='app.Approach')),
                ('specialty', models.ManyToManyField(blank=True, to='app.Specialty')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.status')),
            ],
            options={
                'verbose_name': 'UserProfile',
                'verbose_name_plural': 'UserProfiles',
            },
        ),
    ]
# Generated by Django 2.2.5 on 2020-04-27 16:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20200427_1501'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='moblie',
            new_name='mobile',
        ),
    ]

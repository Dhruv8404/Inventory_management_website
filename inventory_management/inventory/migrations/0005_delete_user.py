# Generated by Django 5.1.3 on 2025-02-09 18:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_user_options_remove_user_username_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]

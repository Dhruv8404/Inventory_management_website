# Generated by Django 5.1.3 on 2025-04-07 19:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_alter_item_name_billpage'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BillPage',
        ),
    ]

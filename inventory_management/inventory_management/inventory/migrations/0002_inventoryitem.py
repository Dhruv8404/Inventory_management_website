# Generated by Django 5.1.3 on 2025-01-25 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=100)),
                ('category', models.CharField(blank=True, max_length=50, null=True)),
                ('quantity', models.IntegerField(default=0)),
                ('unit', models.CharField(default='pcs', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('expiration_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

# Generated by Django 4.2.2 on 2024-01-30 18:29

import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0056_sale_receipt_comments'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(), upload_to='products/photos/'),
        ),
    ]

# Generated by Django 4.2.2 on 2023-07-20 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0015_alter_product_barcode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='barcode',
            field=models.CharField(blank=True, max_length=22, null=True, unique=True),
        ),
    ]

# Generated by Django 4.2.2 on 2023-08-10 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0022_alter_product_barcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='state',
            field=models.CharField(choices=[('sold', 'Vendido'), ('availabel', 'Disponible'), ('reserved', 'reserved'), ('na', 'N/A')], default='availabel', max_length=100),
        ),
    ]

# Generated by Django 4.2.2 on 2024-01-31 03:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0058_report_total_business_report_total_joseph_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='provider_price',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='En colones', max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='remaining',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='sale_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=11, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='total_business',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=11, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='total_joseph',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=11, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='total_mauricio',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=11, null=True),
        ),
        migrations.AlterField(
            model_name='sale',
            name='discount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='sale',
            name='gross_total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='sale',
            name='net_total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='sale',
            name='subtotal',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, help_text='En colones', max_digits=10, null=True),
        ),
    ]

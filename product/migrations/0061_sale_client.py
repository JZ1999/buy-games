# Generated by Django 4.2.2 on 2024-02-08 16:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0010_client'),
        ('product', '0060_sale_platform_sale_shipping'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administration.client'),
        ),
    ]

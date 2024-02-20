# Generated by Django 4.2.2 on 2024-02-20 03:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0010_client'),
        ('product', '0063_product_hidden'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='administration.client'),
        ),
    ]

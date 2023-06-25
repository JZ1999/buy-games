# Generated by Django 4.2.2 on 2023-06-24 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_rename_photo_product_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessory',
            name='console',
            field=models.CharField(choices=[('na', 'N/A'), ('ps1', 'PS1'), ('ps2', 'PS2'), ('ps3', 'PS3'), ('ps4', 'PS4'), ('ps5', 'PS5'), ('wii', 'Wii'), ('wiiu', 'Wii U'), ('n64', 'N64'), ('snes', 'SNES'), ('switch', 'Nintendo Switch')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='console',
            name='title',
            field=models.CharField(choices=[('na', 'N/A'), ('ps1', 'PS1'), ('ps2', 'PS2'), ('ps3', 'PS3'), ('ps4', 'PS4'), ('ps5', 'PS5'), ('wii', 'Wii'), ('wiiu', 'Wii U'), ('n64', 'N64'), ('snes', 'SNES'), ('switch', 'Nintendo Switch')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='videogame',
            name='console',
            field=models.CharField(choices=[('na', 'N/A'), ('ps1', 'PS1'), ('ps2', 'PS2'), ('ps3', 'PS3'), ('ps4', 'PS4'), ('ps5', 'PS5'), ('wii', 'Wii'), ('wiiu', 'Wii U'), ('n64', 'N64'), ('snes', 'SNES'), ('switch', 'Nintendo Switch')], max_length=20, null=True),
        ),
    ]

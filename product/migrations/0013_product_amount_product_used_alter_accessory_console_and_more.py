# Generated by Django 4.2.2 on 2023-07-09 01:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_alter_accessory_console_alter_console_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='amount',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='product',
            name='used',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='accessory',
            name='console',
            field=models.CharField(choices=[('na', 'N/A'), ('ps1', 'PS1'), ('ps2', 'PS2'), ('ps3', 'PS3'), ('ps4', 'PS4'), ('ps5', 'PS5'), ('psvita', 'PSVita'), ('psp', 'PSP'), ('wii', 'Wii'), ('wiiu', 'Wii U'), ('n64', 'N64'), ('snes', 'SNES'), ('nes', 'Nes'), ('gameboy', 'Gameboy'), ('gameboy-color', 'GameboyColor'), ('gameboy-pocket', 'GameboyPocket'), ('gameboy-advanced', 'GameboyAdvanced'), ('gameboy-advanced-sp', 'GameboyAdvancedSP'), ('ds', 'DS'), ('dsi', 'DSi'), ('3ds', '3DS'), ('switch', 'Nintendo Switch')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='console',
            name='title',
            field=models.CharField(choices=[('na', 'N/A'), ('ps1', 'PS1'), ('ps2', 'PS2'), ('ps3', 'PS3'), ('ps4', 'PS4'), ('ps5', 'PS5'), ('psvita', 'PSVita'), ('psp', 'PSP'), ('wii', 'Wii'), ('wiiu', 'Wii U'), ('n64', 'N64'), ('snes', 'SNES'), ('nes', 'Nes'), ('gameboy', 'Gameboy'), ('gameboy-color', 'GameboyColor'), ('gameboy-pocket', 'GameboyPocket'), ('gameboy-advanced', 'GameboyAdvanced'), ('gameboy-advanced-sp', 'GameboyAdvancedSP'), ('ds', 'DS'), ('dsi', 'DSi'), ('3ds', '3DS'), ('switch', 'Nintendo Switch')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='owner',
            field=models.CharField(blank=True, choices=[('joseph', 'Joseph'), ('mauricio', 'Mauricio'), ('business', 'Business')], default='business', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='provider_price',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='En colones', max_digits=8),
        ),
        migrations.AlterField(
            model_name='product',
            name='region',
            field=models.CharField(blank=True, choices=[('jp', 'Japan'), ('usa', 'USA'), ('eu', 'Europe')], default='usa', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='sale_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='En colones', max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='videogame',
            name='console',
            field=models.CharField(choices=[('na', 'N/A'), ('ps1', 'PS1'), ('ps2', 'PS2'), ('ps3', 'PS3'), ('ps4', 'PS4'), ('ps5', 'PS5'), ('psvita', 'PSVita'), ('psp', 'PSP'), ('wii', 'Wii'), ('wiiu', 'Wii U'), ('n64', 'N64'), ('snes', 'SNES'), ('nes', 'Nes'), ('gameboy', 'Gameboy'), ('gameboy-color', 'GameboyColor'), ('gameboy-pocket', 'GameboyPocket'), ('gameboy-advanced', 'GameboyAdvanced'), ('gameboy-advanced-sp', 'GameboyAdvancedSP'), ('ds', 'DS'), ('dsi', 'DSi'), ('3ds', '3DS'), ('switch', 'Nintendo Switch')], max_length=20, null=True),
        ),
    ]
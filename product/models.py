import datetime
from datetime import date, timedelta
from functools import reduce

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib import admin
from django.core.files.storage import DefaultStorage
from django.db import models
import django.conf as conf
import random

from django.db.models import Q

from games.utils.storage_backends import PrivateMediaStorage
from helpers.payment import formatted_number, commission_price, factor_tasa_0, factor_card, PaymentMethodEnum


class RegionEnum(models.TextChoices):
    Japan = "jp", "Japan"
    USA = "usa", "USA"
    Europe = "eu", "Europe"


class StateEnum(models.TextChoices):
    sold = "sold", "Vendido"
    available = "available", "Disponible"
    reserved = "reserved", "Apartado"
    na = "na", "N/A"


class OwnerEnum(models.TextChoices):
    Joseph = "joseph", "Joseph"
    Mauricio = "mauricio", "Mauricio"
    Business = "business", "Business"


class ProviderEnum(models.TextChoices):
    ebay = "ebay", "Ebay"
    tecnoplay = "tecnoplay", "Tecnoplay"
    ali_express = "aliexpress", "AliExpress"
    cliente = "cliente", "Cliente"
    otros = "otros", "Otros"


class ConsoleEnum(models.TextChoices):
    NA = "na", "N/A"
    PlayStation1 = "ps1", "PS1"
    PlayStation2 = "ps2", "PS2"
    PlayStation3 = "ps3", "PS3"
    PlayStation4 = "ps4", "PS4"
    PlayStation5 = "ps5", "PS5"
    PlayStation5Slim = "ps5-slim", "PS5 Slim"
    Xbox = "xbox", "Xbox"
    Xbox360 = "xbox360", "Xbox 360"
    XboxOne = "xbox-one", "Xbox One"
    XboxSeriesS = "xbox-series-s", "Xbox Series S"
    XboxSeriesX = "xbox-series-x", "Xbox Series X"
    PSVita = "psvita", "PSVita"
    PSP = "psp", "PSP"
    Wii = "wii", "Wii"
    WiiU = "wiiu", "Wii U"
    N64 = "n64", "N64"
    Snes = "snes", "SNES"
    Nes = "nes", "NES"
    Atari2600 = "atari2600", "Atari 2600"
    SegaGenesis = "sega-genesis", "Sega Genesis"
    SegaDreamcast = "sega-dreamcast", "Sega Dreamcast"
    SegaSaturn = "sega-saturn", "Sega Saturn"
    SegaNomad = "sega-nomad", "Sega Nomad"
    SegaGameGear = "sega-gamegear", "Sega GameGear"
    Gameboy = "gameboy", "Gameboy"
    GameboyColor = "gameboy-color", "Gameboy Color"
    GameboyPocket = "gameboy-pocket", "Gameboy Pocket"
    GameboyAdvanced = "gameboy-advanced", "Gameboy Advanced"
    GameboyAdvancedSP = "gameboy-advanced-sp", "Gameboy Advanced SP"
    Gamecube = "gamecube", "Gamecube"
    DS = "ds", "DS"
    DSLite = "ds-lite", "DS Lite"
    DSi = "dsi", "DSi"
    _3DS = "3ds", "3DS"
    New3DS = "new-3ds", "New 3DS"
    New3DSXL = "new-3ds-xl", "New 3DS XL"
    _2DS = "2ds", "2DS"
    New2DSXL = "new-2ds-xl", "New 2DS XL"
    Switch = "switch", "Nintendo Switch"
    SwitchOLED = "switch-oled", "Nintendo Switch OLED"
    SwitchLite = "switch-lite", "Nintendo Switch Lite"


class WarrantyType(models.TextChoices):
    STANDARD = "standard", "Standard"
    EXTENDED = "extended", "Extended"


class Console(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    title = models.CharField(
        max_length=20,
        choices=ConsoleEnum.choices,
        null=True
    )

    def __str__(self):
        return self.get_title_display()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.product.amount > 1:
            self.product.duplicate()


class VideoGame(models.Model):
    title = models.CharField(max_length=100, default="")
    console = models.CharField(
        max_length=20,
        choices=ConsoleEnum.choices,
        null=True
    )
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.product.amount > 1:
            self.product.duplicate()


class Collectable(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.product.amount > 1:
            self.product.duplicate()


class Accessory(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="")
    console = models.CharField(
        max_length=20,
        choices=ConsoleEnum.choices,
        null=True
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.product.amount > 1:
            self.product.duplicate()


class Payment(models.Model):
    sale_price = models.DecimalField(max_digits=8, decimal_places=2)
    net_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)
    remaining = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(default=PaymentMethodEnum.na, max_length=100, choices=PaymentMethodEnum.choices,
                                      null=True, blank=True)

    def __str__(self):
        return self.payment_method

    def check_payment(self):
        payment_info = {
            "sale_price": self.remaining,
            "payment_method": self.payment_method,
        }
        if self.payment_method == PaymentMethodEnum.na:
            payment_info.update({
                "tasa0": commission_price(self.remaining, factor_tasa_0()),
                "card": commission_price(self.remaining, factor_card()),
            })

        return payment_info

    @property
    @admin.display(description='sale price', ordering='sale_price')
    def sale_price_formatted(self):
        if self.net_price:
            return formatted_number(self.net_price)

    @property
    @admin.display(description='precio datafono', ordering='sale_price')
    def sale_price_with_card(self):
        if self.net_price:
            return formatted_number(commission_price(self.net_price, factor_card()))

    @property
    @admin.display(description='precio tasa 0', ordering='sale_price')
    def sale_price_with_tasa_0(self):
        if self.net_price:
            return formatted_number(commission_price(self.net_price, factor_tasa_0()))

def food_path(instance, filename):
    return '{0}/{1}'.format(instance.category.name, filename)


class Product(models.Model):
    sale_price = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True,
                                     help_text="En colones")
    provider_price = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, help_text="En colones")
    provider = models.CharField(max_length=200, null=True, blank=True, choices=ProviderEnum.choices)
    remaining = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True,
                                    help_text="En colones")
    barcode = models.CharField(max_length=22, null=True, blank=True, unique=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)
    provider_purchase_date = models.DateField(default=datetime.date.today)
    sale_date = models.DateField(null=True, blank=True)
    owner = models.CharField(default=OwnerEnum.Business, max_length=100, choices=OwnerEnum.choices, null=True,
                             blank=True)
    description = models.TextField(help_text="Descripción que puede ver el cliente")
    notes = models.TextField(default="", help_text="Notas internas", blank=True, null=True)

    region = models.CharField(default=RegionEnum.USA, max_length=100, choices=RegionEnum.choices, null=True, blank=True)
    image = models.ImageField(upload_to='products/photos/', null=True,
                              blank=True, storage=DefaultStorage() if not settings.S3_ENABLED else PrivateMediaStorage())

    amount = models.PositiveIntegerField(default=1, help_text="Se generan copias si pones mas que uno")
    amount_to_notify = models.PositiveIntegerField(null=True, blank=True)

    used = models.BooleanField(default=True)
    state = models.CharField(default=StateEnum.available, max_length=100, choices=StateEnum.choices)

    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.BooleanField(default=False, blank=True, null=True)

    tags = models.ManyToManyField("Tag", related_name="products", blank=True)

    def __str__(self):
        try:
            display = self.get_additional_product_info().get_title_display()
        except:
            try:
                display = self.get_additional_product_info().title
            except:
                return "ERROR sin info adicional"

        return display

    def generate_barcode(self, *args, **kwargs):
        self.barcode = ''.join(random.choice('0123456789') for _ in range(12))

    @property
    @admin.display(description='console')
    def console_type(self):
        try:
            if self.console_set.first():
                return self.console_set.first()
            elif hasattr(self.get_additional_product_info(), "console"):
                return self.get_additional_product_info().get_console_display()
        except:
            return "ERROR no tiene tipo"

    @property
    @admin.display(description='copies')
    def copies(self):
        try:
            return self.get_additional_product_info().__class__.objects.filter(
                title=self.get_additional_product_info().title, product__state=StateEnum.available).count()
        except ValueError:
            return "ERROR"

    @property
    @admin.display(description='sale price', ordering='sale_price')
    def sale_price_formatted(self):
        if self.payment:
            return self.payment.sale_price_formatted

    @property
    @admin.display(description='precio datafono', ordering='sale_price')
    def sale_price_with_card(self):
        if self.payment:
            return self.payment.sale_price_with_card

    @property
    @admin.display(description='precio tasa 0', ordering='sale_price')
    def sale_price_with_tasa_0(self):
        if self.payment:
            return self.payment.sale_price_with_tasa_0

    @property
    @admin.display(description='provider price', ordering='provider_price')
    def provider_price_formatted(self):
        if self.provider_price:
            return f'{self.provider_price:,}₡'

    def get_additional_product_info(self):
        if additional_info := VideoGame.objects.filter(product=self).first():
            return additional_info
        elif additional_info := Console.objects.filter(product=self).first():
            return additional_info
        elif additional_info := Accessory.objects.filter(product=self).first():
            return additional_info
        elif additional_info := Collectable.objects.filter(product=self).first():
            return additional_info
        else:
            raise ValueError("Este producto no tiene informacion adicional")

    def get_product_type(self):
        type_mapping = {
            VideoGame: "Videojuego",
            Collectable: "Collecionable",
            Console: "Consola",
            Accessory: "Accesorio"
        }
        return type_mapping[type(self.get_additional_product_info())]

    def duplicate(self):
        amount = self.amount
        self.amount = 1
        self.save()
        current_tags = self.tags.all()
        for _ in range(amount - 1):
            copy = self

            additional_info = copy.get_additional_product_info()

            copy.pk = None
            copy.payment = None
            copy.amount = 1
            copy.save()

            copy.tags.set(current_tags)
            copy.save()

            additional_info.pk = None
            additional_info.product = copy
            additional_info.save()

    def save(self, *args, **kwargs):

        if not self.payment:
            payment = Payment(sale_price=self.sale_price,
                              net_price=self.sale_price,
                              remaining=self.sale_price)  # TODO falta quitar sle_price de producto
            payment.save()
            self.payment = payment

        if self.state == StateEnum.available:
            self.payment.sale_price = self.sale_price
            self.payment.net_price = self.sale_price
            self.payment.remaining = self.sale_price
            self.remaining = self.sale_price
            self.payment.payment_method = PaymentMethodEnum.na
            self.payment.save()

        if not self.barcode:
            self.generate_barcode()
        else:
            duplicate_products = Product.objects.filter(barcode=self.barcode)

        super().save(*args, **kwargs)

        try:
            if self.amount > 1 and self.get_additional_product_info():
                self.duplicate()
        except ValueError as e:
            pass


class Report(models.Model):
    date = models.DateField()
    total = models.DecimalField(default=0.0, max_digits=11, decimal_places=2, null=True, blank=True,
                                help_text="En colones")
    total_business = models.DecimalField(default=0.0, max_digits=11, decimal_places=2, null=True, blank=True,
                                         help_text="En colones")
    total_mauricio = models.DecimalField(default=0.0, max_digits=11, decimal_places=2, null=True, blank=True,
                                         help_text="En colones")
    total_joseph = models.DecimalField(default=0.0, max_digits=11, decimal_places=2, null=True, blank=True,
                                       help_text="En colones")

    def __str__(self):
        return self.date.strftime('%d de %B de %Y')

    def calculate_total(self):
        yesterday = date.today() - timedelta(days=1)

        if self.date < yesterday:
            return formatted_number(self.total)
        total_value = sum([sale.net_total for sale in self.sale_set.all()])
        self.total = total_value
        self.save()
        return formatted_number(total_value)

    def _calculate_total_for(self, owner: OwnerEnum, params):
        yesterday = date.today() - timedelta(days=1)

        if self.date < yesterday:
            return formatted_number(params['total'] if params['total'] else 0)

        field_keyword = 'payment__net_price'
        remaining_percentage = 0.9 if owner != OwnerEnum.Business else 1

        all_sales = self.sale_set.all()

        list_of_all_products = [
            list(
                sale.products.filter(owner__exact=owner).values(field_keyword)
            ) if sale.products.count() else [{field_keyword: sale.net_total if owner == OwnerEnum.Business else 0}] for sale in all_sales
        ]

        list_of_all_products = reduce(lambda a, b: a + b, list_of_all_products) if len(list_of_all_products) else [{field_keyword: 0}]
        list_of_all_products = [float(total.get(field_keyword)) * remaining_percentage if total.get(field_keyword) else 0 for total in list_of_all_products]

        if owner == OwnerEnum.Business:
            list_of_other_owners_products = [
                list(sale.products.filter(~Q(owner__exact=owner)).values(field_keyword)) for sale in all_sales
            ]
            list_of_other_owners_products = reduce(lambda a, b: a + b, list_of_other_owners_products) if len(list_of_other_owners_products) else [{field_keyword: 0}]
            list_of_other_owners_products = [
                float(total.get(field_keyword)) * 0.1 if total.get(field_keyword) else 0 for total in list_of_other_owners_products
            ]
            list_of_all_products = [*list_of_all_products, *list_of_other_owners_products]

            # Add repairs and requests
        total_value = sum(list_of_all_products)
        setattr(self, params['field'], total_value)
        self.save()
        return formatted_number(total_value)

    @property
    def calculated_total_business(self):
        params = {'total': self.total_business, 'field': 'total_business'}
        return self._calculate_total_for(OwnerEnum.Business, params)

    @property
    def calculated_total_mauricio(self):
        params = {'total': self.total_mauricio, 'field': 'total_mauricio'}
        return self._calculate_total_for(OwnerEnum.Mauricio, params)

    @property
    def calculated_total_joseph(self):
        params = {'total': self.total_joseph, 'field': 'total_joseph'}
        return self._calculate_total_for(OwnerEnum.Joseph, params)


class SaleTypeEnum(models.TextChoices):
    Repair = "repair", "Repair"
    Request = "request", "Request"
    Reserve = "reserve", "Reserve"
    Purchase = "purchase", "Purchase"


class PlatformEnum(models.TextChoices):
    Store = "store", "Store"
    Whatsapp = "whatsapp", "Whatsapp"
    Instagram = "instagram", "Instagram"
    Facebook = "facebook", "Facebook"
    Event = "event", "Event"
    Other = "other", "Other"


class Sale(models.Model):
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    products = models.ManyToManyField(Product)
    warranty_type = models.CharField(max_length=100)
    purchase_date_time = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=100)
    subtotal = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True,
                                   help_text="En colones")
    discount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True,
                                   help_text="En colones")
    taxes = models.DecimalField(default=0.0, max_digits=8, decimal_places=2, null=True, blank=True,
                                help_text="En colones")
    gross_total = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True,
                                      help_text="En colones")
    net_total = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, null=True, blank=True,
                                    help_text="En colones")
    payment_details = models.TextField(blank=True, default="")
    receipt_comments = models.TextField(blank=True, default="")
    customer_name = models.CharField(max_length=100, default="Ready")
    customer_mail = models.EmailField(default='readygamescr@gmail.com')
    creation_date_time = models.DateTimeField(null=True, auto_now_add=True)
    type = models.CharField(max_length=100, default=SaleTypeEnum.Purchase, choices=SaleTypeEnum.choices)
    shipping = models.BooleanField(default=False, help_text="Si es por envio")
    platform = models.CharField(max_length=100, default=PlatformEnum.Store, choices=PlatformEnum.choices)
    client = models.ForeignKey('administration.Client', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if not self.report:
            return ""
        products_str = ", ".join(product.description[:30] for product in self.products.all()[:2])
        if self.type == SaleTypeEnum.Repair:
            products_str = self.payment_details[:30]
        elif not products_str:
            products_str = "ERROR"

        return f"{self.report.date} - {products_str} - ₡{self.gross_total:,}"


class Log(models.Model):
    """
    Saving data to this model about every request
    """

    datetime = models.DateTimeField(auto_now=True)
    status_code = models.PositiveSmallIntegerField()
    status_text = models.TextField()
    response = models.TextField()
    request = models.TextField()
    ipv4_address = models.GenericIPAddressField()
    path = models.CharField(validators=[], max_length=100)
    is_secure = models.BooleanField()

    def __str__(self):
        return f"Log(datetime={self.datetime}, status_code={self.status_code}, path={self.path})"

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        """
        Overriding the save method in order to limit the amount of Logs that can be saved in the database.
        The limit is LOGS_LIMIT, after that the first ones inserted will be eliminated
        """
        super().save()
        count = Log.objects.count()
        extra = count - conf.settings.LOGS_LIMIT
        if extra > 0:
            remainder = Log.objects.all()[:extra]
            for log in remainder:
                log.delete()


class Expense(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.PositiveIntegerField()
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    color = ColorField(default='#00FF00')

    def __str__(self):
        return self.name

import datetime
import sys
from datetime import date, timedelta
from functools import reduce
from io import BytesIO

from PIL import Image
from colorfield.fields import ColorField
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.files.storage import DefaultStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models, Sum
import django.conf as conf
import random

from django.db.models import Q, QuerySet

from games.utils.storage_backends import PrivateMediaStorage
from helpers.payment import formatted_number, commission_price, factor_tasa_0, factor_card, PaymentMethodEnum, \
    factor_tasa_0_10_months
from possimplified.models import Food


class RegionEnum(models.TextChoices):
    Japan = "jp", "Japan"
    USA = "usa", "USA"
    Europe = "eu", "Europe"


class StateEnum(models.TextChoices):
    sold = "sold", "Vendido"
    available = "available", "Disponible"
    reserved = "reserved", "Apartado"
    pending = "pending", "Pago Pendiente"
    na = "na", "N/A"


class ProductTypeEnum(models.TextChoices):
    videogame = "videogame", "Videojuego"
    console = "console", "Consola"
    accessory = "accessory", "Accesorio"
    replacement = "replacement", "Replacement"
    collectable = "collectable", "Collecionable"
    food = "food", "Comida"


class OwnerEnum(models.TextChoices):
    Joseph = "joseph", "Joseph"
    Mauricio = "mauricio", "Mauricio"
    Business = "business", "Business"
    Consignacion = "consignacion", "Consignacion"


class ProviderEnum(models.TextChoices):
    ebay = "ebay", "Ebay"
    tecnoplay = "tecnoplay", "Tecnoplay"
    ali_express = "aliexpress", "AliExpress"
    cliente = "cliente", "Cliente"
    otros = "otros", "Otros"


class ConsoleEnum(models.TextChoices):
    # Sony
    PlayStation1 = "ps1", "PS1"
    PSone = "psone", "PSone"
    PlayStation2 = "ps2", "PS2"
    PS2FAT = "ps2-fat", "PS2 Fat"
    PS2Slim = "ps2-slim", "PS2 Slim"
    PS2Japanese = "ps2-japonés", "PS2 Japanese"
    PlayStation3 = "ps3", "PS3"
    PS3FAT = "ps3-fat", "PS3 Fat"
    PS3Slim = "ps3-slim", "PS3 Slim"
    PS3SuperSlim = "ps3-super-slim", "PS3 Super Slim"
    PlayStation4 = "ps4", "PS4"
    PS4FAT = "ps4-fat", "PS4 Fat"
    PS4Slim = "ps4-slim", "PS4 Slim"
    PS4Pro = "ps4-pro", "PS4 Pro"
    PlayStation5 = "ps5", "PS5"
    PlayStation5Slim = "ps5-slim", "PS5 Slim"
    PlayStation5Pro = "ps5-pro", "PS5 Pro"
    PSP = "psp", "PSP"
    PSP1000 = "psp1000", "PSP1000"
    PSP2000 = "psp2000", "PSP2000"
    PSP3000 = "psp3000", "PSP3000"
    PSPGo = "psp-go", "PSP Go"
    PSVita = "psvita", "PSVita"
    PSClassic = "ps-classic", "PS Classic"

    # Xbox
    Xbox = "xbox", "Xbox"
    Xbox360 = "xbox360", "Xbox 360"
    Xbox360Fat = "xbox360-fat", "Xbox 360 Fat"
    Xbox360Slim = "xbox360-slim", "Xbox 360 Slim"
    Xbox360SlimE = "xbox360-slim-e", "Xbox 360 Slim E"
    XboxOne = "xbox-one", "Xbox One"
    XboxOneFat = "xbox-one-fat", "Xbox One Fat"
    XboxOneS = "xbox-one-s", "Xbox One S"
    XboxOneX = "xbox-one-x", "Xbox One X"
    XboxSeriesS = "xbox-series-s", "Xbox Series S"
    XboxSeriesX = "xbox-series-x", "Xbox Series X"

    # Nintendo
    Switch2 = "switch2", "Nintendo Switch 2"
    Switch = "switch", "Nintendo Switch"
    SwitchOLED = "switch-oled", "Nintendo Switch OLED"
    SwitchLite = "switch-lite", "Nintendo Switch Lite"
    Gamecube = "gamecube", "Gamecube"
    Gameboy = "gameboy", "Gameboy"
    GameboyDMG = "gameboy-dmg", "Gameboy DMG"
    GameboyColor = "gameboy-color", "Gameboy Color"
    GameboyPocket = "gameboy-pocket", "Gameboy Pocket"
    GameboyAdvanced = "gameboy-advanced", "Gameboy Advanced"
    GameboyAdvancedSP = "gameboy-advanced-sp", "Gameboy Advanced SP"
    GameboyMicro = "gameboy-micro", "Gameboy Micro"
    DS = "ds", "DS"
    DSLite = "ds-lite", "DS Lite"
    DSi = "dsi", "DSi"
    DSiXL = "dsi-xl", "DSi XL"
    _3DS = "3ds", "3DS"
    _3DS_XL = "3ds-xl", "3DS XL"
    New3DS = "new-3ds", "New 3DS"
    New3DSXL = "new-3ds-xl", "New 3DS XL"
    _2DS = "2ds", "2DS"
    New2DSXL = "new-2ds-xl", "New 2DS XL"
    Wii = "wii", "Wii"
    WiiU = "wiiu", "Wii U"
    WiiMini = "wii-mini", "Wii Mini"
    N64 = "n64", "N64"
    Snes = "snes", "SNES"
    SuperFamicom = "super-famicom", "Super Famicom"
    SnesJunior = "snes-junior", "SNES Junior"
    SnesMini = "snes-mini", "SNES Mini"
    Nes = "nes", "NES"
    NesTopLoader = "nes-top-loader", "NES Top Loader"
    Famicom = "famicom", "Famicom"
    NesMini = "nes-mini", "NES Mini"

    # Sega
    SegaMasterSystem = "sega-master-system", "Sega Master System"
    SegaGenesis = "sega-genesis", "Sega Genesis (Modelo 1)"
    SegaGenesis2 = "sega-genesis-2", "Sega Genesis (Modelo 2)"
    SegaGenesis3 = "sega-genesis-3", "Sega Genesis (Modelo 3)"
    SegaGenesisMini = "sega-genesis-mini", "Sega Genesis Mini"
    SegaDreamcast = "sega-dreamcast", "Sega Dreamcast"
    SegaSaturn = "sega-saturn", "Sega Saturn"
    SegaNomad = "sega-nomad", "Sega Nomad"
    SegaGameGear = "sega-gamegear", "Sega GameGear"

    # Atari
    Atari2600 = "atari2600", "Atari 2600"

    # Other
    PC = "pc", "PC"
    Mobile = "mobile", "Celular/Tablet"
    Other = "other", "Otros"
    NeoGeoPocket = "neogeo-pocket", "NeoGeo Pocket"


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

    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.get_title_display()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.product.type = ProductTypeEnum.console
        self.product.save()

        if self.product.amount > 1:
            self.product.duplicate()


class Replacement(models.Model):
    title = models.CharField(max_length=100, default="")
    console = models.CharField(
        max_length=20,
        choices=ConsoleEnum.choices,
        null=True
    )
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.product.type = ProductTypeEnum.replacement
        self.product.save()

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

    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.product.type = ProductTypeEnum.videogame
        self.product.save()

        if self.product.amount > 1:
            self.product.duplicate()


class Collectable(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=100)

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.product.type = ProductTypeEnum.collectable
        self.product.save()

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

    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.product.type = ProductTypeEnum.accessory
        self.product.save()

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

    @property
    @admin.display(description='precio tasa 0 (10 meses)', ordering='sale_price')
    def sale_price_with_tasa_0_10_months(self):
        if self.net_price:
            return formatted_number(commission_price(self.net_price, factor_tasa_0_10_months()))


class Product(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)

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
                              blank=True,
                              storage=DefaultStorage() if not settings.S3_ENABLED else PrivateMediaStorage())

    amount = models.PositiveIntegerField(default=1, help_text="Se generan copias si pones mas que uno")
    amount_to_notify = models.PositiveIntegerField(null=True, blank=True)

    used = models.BooleanField(default=True)
    state = models.CharField(default=StateEnum.available, max_length=100, choices=StateEnum.choices)
    type = models.CharField(default=ProductTypeEnum.videogame, max_length=100, choices=ProductTypeEnum.choices)
    hidden = models.BooleanField(default=False, help_text="Used mainly to hide duplicate products")

    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.BooleanField(default=False, blank=True, null=True)

    tags = models.ManyToManyField("Tag", related_name="products", blank=True)

    location = models.ForeignKey("administration.Location", blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['used']),
            models.Index(fields=['state']),
            models.Index(fields=['hidden']),
        ]

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

    def similar_products(self, equal_state: bool = True):
        try:
            additional_info = self.get_additional_product_info()
            queryset_additional_info: QuerySet = additional_info.__class__.objects
        except (ValueError, AttributeError):
            return []

        search_term = additional_info.title

        # Filtering logic based on additional_info's class
        if additional_info.__class__ in [Console, Accessory, VideoGame, Replacement]:
            if additional_info.__class__ == Console:
                queryset_additional_info = queryset_additional_info.filter(title=additional_info.title)
            else:
                queryset_additional_info = queryset_additional_info.filter(console=additional_info.console)

        # Base filtering logic
        queryset_additional_info = queryset_additional_info.filter(
            Q(title__iexact=search_term) | Q(product__barcode__exact=self.barcode)
        )

        # Conditionally filter by state based on equal_state
        if equal_state:
            queryset_additional_info = queryset_additional_info.filter(product__state=self.state)

        # Exclude invalid entries
        additional_info = [i for i in queryset_additional_info if not isinstance(i, str)]

        return additional_info

    def equal_products(self):
        try:
            additional_info = self.get_additional_product_info()
            queryset_additional_info: QuerySet = additional_info.__class__.objects
        except (ValueError, AttributeError):
            return "ERROR"

        search_term = additional_info.title
        if additional_info.__class__ == Console:
            queryset_additional_info = queryset_additional_info.filter(
                title=search_term,
                product__description=self.description,
                product__barcode=self.barcode
            )
        elif additional_info.__class__ == Collectable:
            pass
        else:
            queryset_additional_info = queryset_additional_info.filter(console=additional_info.console)
        queryset_additional_info = queryset_additional_info.filter(product__state=self.state). \
            filter(Q(title__iexact=search_term) & Q(product__barcode__exact=self.barcode) &
                   Q(product__description__iexact=self.description))

        additional_info = [i for i in queryset_additional_info if not isinstance(i, str)]

        return additional_info

    @property
    @admin.display(description='copies')
    def copies(self):
        similar_products_result = self.similar_products()

        if type(similar_products_result) != str:
            return len(similar_products_result)
        return similar_products_result

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
    @admin.display(description='precio tasa 0 (10 meses)', ordering='sale_price')
    def sale_price_with_tasa_0_10_months(self):
        if self.payment:
            return self.payment.sale_price_with_tasa_0_10_months

    @property
    @admin.display(description='provider price', ordering='provider_price')
    def provider_price_formatted(self):
        if self.provider_price:
            return f'{self.provider_price:,}₡'

    def get_additional_product_info(self):
        if self.type == ProductTypeEnum.videogame:
            return self.videogame_set.first()
        elif self.type == ProductTypeEnum.console:
            return self.console_set.first()
        elif self.type == ProductTypeEnum.accessory:
            return self.accessory_set.first()
        elif self.type == ProductTypeEnum.collectable:
            return self.collectable_set.first()
        elif self.type == ProductTypeEnum.replacement:
            return self.replacement_set.first()
        elif self.type == ProductTypeEnum.food:
            return self.food_set.first()
        else:
            raise ValueError("Este producto no tiene informacion adicional")

    def get_product_type(self):
        type_mapping = {
            VideoGame: "Videojuego",
            Replacement: "Repuesto",
            Collectable: "Collecionable",
            Console: "Consola",
            Accessory: "Accesorio",
            Food: "Comida"
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
            copy.hidden = True
            copy.save()

            copy.tags.set(current_tags)
            copy.save()

            additional_info.pk = None
            additional_info.product = copy
            additional_info.save()

    def assign_image_from_similar_products(self):
        if similar_products := self.similar_products(equal_state=False):
            for product in similar_products:
                if product.product.image:
                    self.image = product.product.image
                    break

    def optimize_image(self):
        if self.image and self.image.size > 500 * 1024:  # 500 KB
            img = Image.open(self.image)

            # Convert to RGB if it's a .png or has alpha channel
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            output = BytesIO()
            img.save(output, format='WEBP', quality=30)
            output.seek(0)

            self.image = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{self.image.name.split('.')[0]}.webp",
                'image/webp',
                sys.getsizeof(output),
                None
            )

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
        elif not Product.objects.filter(barcode__exact=self.barcode, state=StateEnum.available, hidden=False):
            if next_product_to_show := Product.objects.filter(barcode__exact=self.barcode,
                                                              state=StateEnum.available, hidden=True).first():
                next_product_to_show.hidden = False
                next_product_to_show.save()
        if not self.barcode:
            self.generate_barcode()

        if not self.image and self.pk:
            self.assign_image_from_similar_products()
        else:
            self.optimize_image()
            
        super().save(*args, **kwargs)

        try:
            if self.get_additional_product_info():
                if self.amount > 1:
                    self.duplicate()

        except ValueError:
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
    total_consignment = models.DecimalField(default=0.0, max_digits=11, decimal_places=2, null=True, blank=True,
                                       help_text="En colones")

    def __str__(self):
        return self.date.strftime('%d de %B de %Y')

    def calculate_total(self):
        yesterday = date.today() - timedelta(days=1)

        #if self.date < yesterday and self.total:
        #    return formatted_number(self.total)
        
        total_value = self.sale_set.exclude(Q(type=SaleTypeEnum.Pending) | Q(type=SaleTypeEnum.Cancelled)) \
                               .aggregate(total=Sum('net_total'))['total'] or 0
        self.total = total_value
        self.save(update_fields=['total'])

        return formatted_number(total_value)

    def _calculate_total_for(self, owner: OwnerEnum, params):
        yesterday = date.today() - timedelta(days=1)

        #if self.date < yesterday and params.get('total'):
        #    return formatted_number(params['total'])
        
        field_keyword = 'payment__net_price'

        remaining_percentage = 0.9 if owner not in (OwnerEnum.Business, OwnerEnum.Consignacion) else 1

        all_sales = self.sale_set.exclude(Q(type=SaleTypeEnum.Pending) | Q(type=SaleTypeEnum.Cancelled) )

        list_of_all_products = [
            list(
                sale.products.filter(owner__exact=owner).values(field_keyword)
            ) if sale.products.count() else [{field_keyword: sale.net_total if owner == OwnerEnum.Business else 0}] for
            sale in all_sales
        ]

        list_of_all_products = reduce(lambda a, b: a + b, list_of_all_products) if len(list_of_all_products) else [
            {field_keyword: 0}]
        list_of_all_products = [
            float(total.get(field_keyword)) * remaining_percentage if total.get(field_keyword) else 0 for total in
            list_of_all_products]

        if owner == OwnerEnum.Business:
            list_of_other_owners_products = [
                list(sale.products.filter(~Q(owner__exact=owner)).values(field_keyword)) for sale in all_sales
            ]
            list_of_other_owners_products = reduce(lambda a, b: a + b, list_of_other_owners_products) if len(
                list_of_other_owners_products) else [{field_keyword: 0}]
            list_of_other_owners_products = [
                float(total.get(field_keyword)) * 0.1 if total.get(field_keyword) else 0 for total in
                list_of_other_owners_products
            ]
            list_of_all_products = [*list_of_all_products, *list_of_other_owners_products]

            # Add repairs and requests
        total_value = sum(list_of_all_products)
        setattr(self, params['field'], total_value)
        self.save(update_fields=[params['field']])
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

    @property
    def calculated_total_consignment(self):
        params = {'total': self.total_joseph, 'field': 'total_consignment'}
        return self._calculate_total_for(OwnerEnum.Consignacion, params)


class SaleTypeEnum(models.TextChoices):
    Repair = "repair", "Repair"
    Request = "request", "Request"
    Reserve = "reserve", "Reserve"
    Purchase = "purchase", "Purchase"
    Pending = "pending", "Pending"
    Cancelled = "cancelled", "Cancelled"


class PlatformEnum(models.TextChoices):
    Store = "store", "Store"
    Whatsapp = "whatsapp", "Whatsapp"
    Instagram = "instagram", "Instagram"
    Facebook = "facebook", "Facebook"
    Event = "event", "Event"
    Online = "online", "Online"
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
    payments_completed = models.BooleanField(default=True, help_text="Si ya termino de pagar el producto")

    payment_details = models.TextField(blank=True, default="")
    receipt_comments = models.TextField(blank=True, default="")
    customer_name = models.CharField(max_length=100, default="Ready")
    customer_mail = models.EmailField(default='readygamescr@gmail.com')

    creation_date_time = models.DateTimeField(null=True, auto_now_add=True)

    type = models.CharField(max_length=100, default=SaleTypeEnum.Purchase, choices=SaleTypeEnum.choices)

    shipping = models.BooleanField(default=False, help_text="Si es por envio")
    sent = models.BooleanField(default=False, help_text="Si ya se envio")

    platform = models.CharField(max_length=100, default=PlatformEnum.Store, choices=PlatformEnum.choices)
    client = models.ForeignKey('administration.Client', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="purchases")

    onvo_pay_payment_intent_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        if not self.report:
            return ""
        products_str = ", ".join(product.description[:30] for product in self.products.all()[:2])
        if self.type == SaleTypeEnum.Repair:
            products_str = self.payment_details[:30]
        elif not products_str:
            products_str = "ERROR"

        price = self.type if self.type in (SaleTypeEnum.Pending, SaleTypeEnum.Cancelled) else f"₡{self.gross_total:,}"

        return f"{self.report.date} - {products_str} - {price}"


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
    internal = models.BooleanField(default=False, help_text="Si es interno, entonces solo se muestra en la pagina" \
                                                            "administrativa, en la pagina web no ni el excel por ejemplo")

    def __str__(self):
        return self.name

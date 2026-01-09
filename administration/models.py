import random
import sys
from datetime import datetime
from io import BytesIO

from PIL import Image
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from bs4 import BeautifulSoup
import requests

from games.utils.storage_backends import PrivateMediaStorage
from product.models import ProviderEnum
from django.core.exceptions import ValidationError
from django.db import transaction

# limits
VIDEO_MAX_SIZE = int(18 * 1024 * 1024)  # 18 MB
ACTIVE_NON_CAROUSEL_LIMIT = 4
# no raw SQL/advisory locks: use ORM + transactions on create


class RequestStateEnum(models.TextChoices):
    purchased = "purchased", "Purchased"
    in_transit = "in_transit", "In Transit"
    in_transit_wfbox = "in_transit_with_wfbox", "In Transit with WfBox"
    not_found = "not_found", "Not Found"
    received = "received", "Received"
    na = "na", "N/A"

class Request(models.Model):
    item_name = models.CharField(max_length=255)
    tracking_number = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(default=ProviderEnum.ebay, max_length=100, choices=ProviderEnum.choices)
    status = models.CharField(default=RequestStateEnum.purchased, max_length=100, choices=RequestStateEnum.choices)

    wf_box_number = models.CharField(max_length=255, null=True, blank=True)
    wf_box_received_datetime = models.DateTimeField(null=True, blank=True)
    weight = models.PositiveSmallIntegerField(null=True, blank=True)
    items = models.PositiveSmallIntegerField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} - {self.tracking_number}"

    def track_wfbox(self):
        headers = {
            'authority': 'intertrade.cargotrack.net',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,es-US;q=0.8,es;q=0.7,fr-FR;q=0.6,fr;q=0.5',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://intertrade.cargotrack.net',
            'pragma': 'no-cache',
            'referer': 'https://intertrade.cargotrack.net/m/track.asp',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'iframe',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }
        data = {
            'track': self.tracking_number,
            'action2': 'process',
        }
        response = requests.post('https://intertrade.cargotrack.net/m/track.asp', headers=headers, data=data)
        html = BeautifulSoup(response.content.decode())
        important_tags = html.findAll("strong")
        if important_tags[3].text == "NOT FOUND":
            self.status = RequestStateEnum.not_found
            self.wf_box_number = None
            self.wf_box_received_datetime = None
            self.items = None
            self.weight = None
        elif important_tags[3].text == "IN TRANSIT":
            self.status = RequestStateEnum.in_transit_wfbox
            self.wf_box_number = important_tags[6].text
            date_format = "%m/%d/%Y %I:%M:%S %p"

            converted_date = datetime.strptime(f"{important_tags[4].text} {important_tags[5].text}", date_format)
            self.wf_box_received_datetime = converted_date
            self.items = important_tags[7].text
            self.weight = important_tags[8].text.split()[0]

        self.save()
        return self.status


class CouponTypeEnum(models.TextChoices):
    percentage = "percentage", "Percentage %"
    fixed = "fixed", "Fixed"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=100, choices=CouponTypeEnum.choices, default=CouponTypeEnum.percentage)
    amount = models.PositiveIntegerField(default=0)
    expiration = models.DateTimeField()
    uses = models.PositiveSmallIntegerField(default=1)


    def __str__(self):
        return self.code

    def save(
        self, *args, **kwargs
    ):
        if not self.code:
            self.code = ''.join(random.choice('0123456789') for _ in range(12))

        super().save(*args, **kwargs)


class Client(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=100)
    _id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)


    def __str__(self):
        return f"{self.full_name.title()} - {self.email}"


class Location(models.Model):
    """
    Used to locate products
    """
    floor = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=200)
    details = models.CharField(max_length=200, help_text="Por ejemplo: Primer Gabeta", blank=True, null=True)
    location_image = models.ImageField(
        upload_to='location/photos/', null=True, blank=True,
        storage=DefaultStorage() if not settings.S3_ENABLED else PrivateMediaStorage()
    )


    def __str__(self):
        return f"{self.name} - Piso: {self.floor} {'('+self.details+')' if self.details else ''}"


class Setting(models.Model):
    disable_online_purchase = models.BooleanField(default=False)

    def __str__(self):
        return "Configuraciones"


class News(models.Model):
    """Represents a news item displayed on the homepage.

    - Either `image` or `video` can be set (prefer image for small media).
    - `is_carousel` marks whether the item belongs in the secondary/carousel area.
    - Image optimization reuses the project's WEBP conversion logic when image > 500KB.
    """
    title = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='news/photos/',
        null=True,
        blank=True,
        storage=DefaultStorage() if not settings.S3_ENABLED else PrivateMediaStorage()
    )
    video = models.FileField(
        upload_to='news/videos/',
        null=True,
        blank=True,
        storage=DefaultStorage() if not settings.S3_ENABLED else PrivateMediaStorage()
    )

    # Optional clickable URL for news items (frontend can open this when the item is clicked)
    link = models.URLField(max_length=500, null=True, blank=True)

    # When True it will be part of the carousel (secondary scroller). On homepage initial grid
    # the site shows at most 4 items (front-end enforces this). Use `order` for manual ordering.
    is_carousel = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-creation_date",)
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        indexes = [models.Index(fields=['is_carousel']), models.Index(fields=['-creation_date'])]

    def __str__(self):
        return self.title or f"News #{self.pk}"

    def optimize_image(self):
        """Convert heavy images to WEBP (same logic used by `product.Product.optimize_image`)."""
        if self.image and getattr(self.image, 'size', 0) > 500 * 1024:  # 500 KB
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

    def validate_video_size(self):
        """Raise ValidationError if `video` exceeds `VIDEO_MAX_SIZE`.

        This is called from `save()` to provide immediate, clear validation
        when creating or updating a `News` instance.
        """
        if not self.video:
            return

        try:
            size = getattr(self.video, 'size', None)
        except Exception:
            size = None

        if size is not None and size > VIDEO_MAX_SIZE:
            raise ValidationError({
                'video': f"Video exceeds maximum allowed size of {VIDEO_MAX_SIZE} bytes ({VIDEO_MAX_SIZE/1024/1024:.1f} MB)."
            })

    def save(self, *args, **kwargs):
        # Validate video size early and raise a proper ValidationError
        self.validate_video_size()

        # Run model validation (includes other checks)
        self.full_clean()

        # Only enforce the "max active non-carousel" rule when creating a new News item
        is_create = self.pk is None
        if is_create and self.active and not self.is_carousel:
            # Transactional check using ORM + select_for_update to reduce race windows.
            with transaction.atomic():
                count = News.objects.select_for_update().filter(active=True, is_carousel=False).count()
                if count >= ACTIVE_NON_CAROUSEL_LIMIT:
                    raise ValidationError({
                        '__all__': f"There can be at most {ACTIVE_NON_CAROUSEL_LIMIT} active non-carousel news items (current: {count})."
                    })
                # safe to optimize and save inside the same transaction
                self.optimize_image()
                super().save(*args, **kwargs)
                return

        # Default path (updates or non-limited cases)
        self.optimize_image()
        super().save(*args, **kwargs)

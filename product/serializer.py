from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static
from rest_framework import serializers
from django.core.validators import RegexValidator
from rest_framework.fields import CharField, SerializerMethodField, URLField

from product.models import Product, Collectable, VideoGame, Accessory, Console, Report, Sale, Payment, Tag, Replacement, \
    PlatformEnum


def create_product(validated_data):
    nested_data = validated_data['product']
    if nested_data is not None:
        validated_data["product"] = Product.objects.create(**nested_data)
    return validated_data


class CollectableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collectable
        fields = "__all__"

    def create(self, validated_data):
        return super().create(create_product(validated_data))


class VideoGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoGame
        fields = "__all__"

    def create(self, validated_data):
        return super().create(create_product(validated_data))


class ReplacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Replacement
        fields = "__all__"

    def create(self, validated_data):
        return super().create(create_product(validated_data))


class AccessorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Accessory
        fields = "__all__"

    def create(self, validated_data):
        return super().create(create_product(validated_data))


class ConsoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Console
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['title'] = instance.get_title_display()
        return representation

    def create(self, validated_data):
        return super().create(create_product(validated_data))


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

    def to_representation(self, instance):
        payment_info = instance.check_payment()
        return payment_info


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class FullURLField(serializers.URLField):
    def to_representation(self, value):
        request = self.context.get('request', None)
        scheme = 'https://'

        current_site = get_current_site(request) if request else None
        domain = current_site.domain if current_site else ''

        full_url = f'{scheme}{domain}/media/{value}'
        if not value:
            full_url = f'{scheme}{domain}{static("assets/common/default.jpg")}'
        return super().to_representation(full_url)



class ProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    price = SerializerMethodField()
    name = SerializerMethodField()
    videogame_set = VideoGameSerializer(many=True)
    replacement_set = ReplacementSerializer(many=True)
    console_set = ConsoleSerializer(many=True)
    collectable_set = CollectableSerializer(many=True)
    accessory_set = AccessorySerializer(many=True)
    type = SerializerMethodField()
    state = serializers.CharField()
    payment = PaymentSerializer(required=True)
    image = SerializerMethodField()
    console = SerializerMethodField()
    tags = TagsSerializer(many=True)

    class Meta:
        model = Product
        fields = ["payment", "barcode", "name", "price", "description", "videogame_set",
                  "console_set", "accessory_set", "collectable_set", "replacement_set", "type", "state", "image", "id",
                  "console", "tags", "used"]

    def get_type(self, obj: Product):
        try:
            return obj.get_product_type()
        except:
            return "N/A"

    def get_price(self, obj: Product):
        return obj.sale_price

    def get_name(self, obj: Product):
        return str(obj)

    def get_console(self, obj: Product):
        if type(obj.get_additional_product_info()) == Collectable or not obj.get_additional_product_info():
            console_code = ""
        else:
            console_code = obj.get_additional_product_info().title if type(
                obj.get_additional_product_info()) == Console else obj.get_additional_product_info().console
        return {"console": str(obj.console_type), "console-code": console_code}

    def get_tags(self, obj: Product):
        return [str(tag) for tag in obj.tags.all()]

    def get_image(self, obj: Product):
        request = self.context.get('request', None)
        scheme = 'https://'

        current_site = get_current_site(request) if request else None
        domain = current_site.domain if current_site else ''

        full_url = f'{scheme}{domain}{static("assets/common/default.jpg")}'
        if obj.image:
            full_url = obj.image.url
        return full_url


class ProductSerializerToShow(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class SaleSerializer(serializers.ModelSerializer):
    products = ProductSerializerToShow(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'


class GenerateBillSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, default=None)
    store_name = serializers.CharField()
    store_address = serializers.CharField()
    store_contact = serializers.CharField()
    store_mail = serializers.EmailField()
    receipt_number = serializers.CharField(required=False)
    purchase_date = serializers.DateField(input_formats=['%d/%m/%Y'])
    customer_name = serializers.CharField()
    customer_mail = serializers.EmailField()
    customer_phone = serializers.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d{8}$',
                message='El número de teléfono debe tener 8 dígitos.',
                code='invalid_phone_number'
            ),
        ])
    platform = serializers.CharField(required=False, default=PlatformEnum.Other)
    payment_method = serializers.CharField()
    items = serializers.ListField()
    payment_details = serializers.CharField(required=False, default="")
    receipt_comments = serializers.CharField(required=False, default="")
    return_policy = serializers.IntegerField(min_value=0, max_value=3)
    order = serializers.BooleanField(required=False, default=False)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    taxes = serializers.DecimalField(required=False, default=0, max_digits=10, decimal_places=2, min_value=0)
    discounts = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    shipping = serializers.BooleanField(required=False, default=False)

    online_payment = serializers.BooleanField(required=False, default=False)
    onvo_pay_payment_intent_id = serializers.CharField(required=False, default="")
    voucher = serializers.FileField(required=False, allow_null=True)

    def validate_voucher_requirements(self, online_payment, voucher):
        """
        Validate that voucher is provided when online_payment is True.
        """
        if online_payment and not voucher:
            raise serializers.ValidationError(
                "Voucher is required for online payments."
            )

    def validate(self, data):
        """
        Custom validation for voucher requirements.
        """
        online_payment = data.get('online_payment', False)
        voucher = data.get('voucher')
        
        self.validate_voucher_requirements(online_payment, voucher)
        
        return data

    def __getattr__(self, item):
        """
        Allows direct attribute access on a validated serializer.
        Example: serializer.discounts instead of serializer.validated_data['discounts'].
        Requires that is_valid() has been called so that _validated_data is set.
        """
        try:
            # Access the internal _validated_data directly.
            validated_data = object.__getattribute__(self, "_validated_data")
        except AttributeError:
            # _validated_data isn't set, so re-raise a standard attribute error.
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            )

        if item in validated_data:
            return validated_data[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")


class ReportSerializer(serializers.ModelSerializer):
    sales = SaleSerializer(many=True, read_only=True, source='sale_set')

    class Meta:
        model = Report
        fields = '__all__'


class ProductStateByIdSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Lista de IDs de productos"
    )
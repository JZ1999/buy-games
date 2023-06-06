from rest_framework import serializers

from product.models import Product, Collectable, VideoGame


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


# Price Barcode Departure date


class CollectableSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Collectable
        fields = "__all__"

    def create(self, validated_data):
        nested_data = validated_data['product']

        if nested_data is not None:
            validated_data["product"] = Product.objects.create(
                price=nested_data["price"],
                barcode=nested_data["barcode"],
                departure_date=nested_data["departure_date"])

        instance = super().create(validated_data)
        return instance


class VideoGameSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = VideoGame
        fields = "__all__"

    def create(self, validated_data):
        nested_data = validated_data['product']

        if nested_data is not None:
            validated_data["product"] = Product.objects.create(
                price=nested_data["price"],
                barcode=nested_data["barcode"],
                departure_date=nested_data["departure_date"])

        instance = super().create(validated_data)
        return instance

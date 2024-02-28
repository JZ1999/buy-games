from django import forms
from django.utils.html import format_html

from product.models import Sale, Product


class ProductsField(forms.Field):
    pass


class SaleInlineForm(forms.ModelForm):

    receipt_products = forms.CharField(max_length=10000, label='Receipt Products', widget=forms.Textarea(attrs={'rows': 10, 'cols': 45}))


    class Meta:
        model = Sale
        exclude = ("products", )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.id:
            # Set the custom value based on the parent object (obj)
            self.initial['receipt_products'] = self._receipt_products(self.instance)

    def format_product_string(self, product: Product):
        return f"{str(product)} - {product.console_type} - ₡{product.payment.net_price if product.payment else self.instance.net_total} - {product.owner} - ID: {product.id} \n"

    def _receipt_products(self, obj: Sale):
        products_string = [ self.format_product_string(product) for product in obj.products.all() ]
        return " ".join(products_string)

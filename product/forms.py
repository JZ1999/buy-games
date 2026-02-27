from django import forms
from django.forms import CheckboxSelectMultiple
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from product.models import Sale, Product


class ProductsField(forms.Field):
    pass


class ColoredCheckboxSelectMultiple(CheckboxSelectMultiple):
    template_name = "django/forms/widgets/tags_checkbox.html"
    option_template_name = "django/forms/widgets/tags_checkbox_option.html"

    def create_option(
            self, *args, **kwargs
    ):
        result = super().create_option(*args, **kwargs)
        tag = args[1].instance
        if tag_color := tag.color:
            result['attrs']['label'] = {}
            result['attrs']['label']['style'] = (f'background-color: {tag_color};'
                                                 f' margin-top: 5px;border-radius: 10px;'
                                                 f'padding-left: 5px')
            # Add 'internal' group info
            result['group'] = 'Internos' if tag.internal else 'Normales'

            return result

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Group options by 'group'
        grouped_options = {}
        for group, options, index in context['widget']['optgroups']:
            for option in options:
                group_name = option['group']
                if group_name not in grouped_options:
                    grouped_options[group_name] = []
                grouped_options[group_name].append(option)

        context['widget']['grouped_options'] = grouped_options
        return context


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'tags': ColoredCheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super(ProductAdminForm, self).__init__(*args, **kwargs)

        if False:
            self.fields['amount_to_notify'].widget = forms.HiddenInput()
            self.fields['type'].widget = forms.HiddenInput()
            self.fields['hidden'].widget = forms.HiddenInput()
            self.fields['order'].widget = forms.HiddenInput()
            self.fields['payment_link'].widget = forms.HiddenInput()
            self.fields['remaining'].widget = forms.HiddenInput()
            self.fields['provider_purchase_date'].widget = forms.HiddenInput()


class DivWidget(forms.Widget):
    """Custom widget to render text inside a div."""
    def render(self, name, value, attrs=None, renderer=None):
        # Ensure the value is safe HTML
        return mark_safe(f"<div>{value or ''}</div>")


class SaleInlineForm(forms.ModelForm):
    receipt_products = forms.Field(
        label='Receipt Products',
        required=False,
        widget=DivWidget()
    )

    class Meta:
        model = Sale
        exclude = ("products", )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.id:
            # Set the custom value based on the parent object (obj)
            self.fields['receipt_products'].initial = self._receipt_products(self.instance)
        self._manage_voucher_field_visibility()

    def format_product_string(self, product: Product):
        product_url = reverse('admin:product_product_change', args=[product.pk])
        net_price = product.payment.net_price if product.payment else self.instance.net_total
        owner = product.owner
        console_type = product.console_type
        product_string = (f"<li style='width: 33rem;'>{str(product)} - {console_type} - ₡{net_price} - {owner} - ID: "
                          f"<a href='{product_url}'>{product.pk}</a> </li>\n")
        return mark_safe(product_string)

    def _receipt_products(self, obj: Sale):
        products_string = [self.format_product_string(product) for product in obj.products.all()]
        return mark_safe(f'<ul>{"".join(products_string)}</ul>')

    def _manage_voucher_field_visibility(self):
        """Manage voucher field."""
        if 'voucher' not in self.fields:
            return
        # Voucher is now optional
        self.fields['voucher'].required = False


class SaleAdminForm(forms.ModelForm):
    """
    Custom form for Sale admin that conditionally displays voucher field.
    Voucher is only shown when:
    - platform is 'online'
    - payment_method is 'card' or 'transfer'
    """
    
    class Meta:
        model = Sale
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manage_voucher_field_visibility()
    
    def _manage_voucher_field_visibility(self):
        """Manage voucher field."""
        if 'voucher' not in self.fields:
            return
        # Voucher is now optional
        self.fields['voucher'].required = False

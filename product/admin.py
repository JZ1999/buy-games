import calendar
import datetime
from collections import defaultdict
from io import BytesIO

import requests
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import StackedInline
from django.db.models import Q
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from unidecode import unidecode

from games.admin import admin_site
from helpers.business_information import business_information
from helpers.payment import formatted_number, PaymentMethodEnum
from possimplified.models import Food
from product.filters import SoldFilter, TypeFilter, ConsoleTitleFilter, BelowThreshHoldFilter, DuplicatesFilter, \
    ToBeShippedFilter, PaymentPendingFilter, WeekdayFilter, WithoutImageFilter, UserSalesFilter
from product.forms import SaleInlineForm, ProductAdminForm, SaleAdminForm
from product.models import Product, Collectable, Console, VideoGame, Accessory, Report, Sale, Log, \
    StateEnum, Expense, Payment, Tag, SaleTypeEnum, Replacement
from django.utils.html import format_html
from django.template.loader import render_to_string
from helpers.qr import qrOptions, qrLinkOptions
from ui.views import GenerateBill, SendMailError


class VideoGamesInline(StackedInline):
    model = VideoGame
    extra = 0
    min_num = 0
    max_num = 1


class ReplacementsInline(StackedInline):
    model = Replacement
    extra = 0
    min_num = 0
    max_num = 1


class CollectableInline(StackedInline):
    model = Collectable
    extra = 0
    min_num = 0
    max_num = 1


class ConsoleInline(StackedInline):
    model = Console
    extra = 0
    min_num = 0
    max_num = 1


class AccessoryInline(StackedInline):
    model = Accessory
    extra = 0
    min_num = 0
    max_num = 1

class FoodInline(StackedInline):
    model = Food
    extra = 0
    min_num = 0
    max_num = 1


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        "__str__", "tipo", "console_type", "description", 'copies', "_state", "sale_price_formatted",
        "sale_price_with_card", "sale_price_with_tasa_0", "sale_price_with_tasa_0_10_months",
        'used_display', 'owner', 'etiquetas', 'image')
    model = Product
    list_filter = (WithoutImageFilter, DuplicatesFilter, SoldFilter, TypeFilter, BelowThreshHoldFilter,
                   ConsoleTitleFilter, 'used', 'creation_date', 'provider', 'owner', 'tags',)
    inlines = []
    actions = ['set_location']
    search_fields = ["videogame__title", "barcode", "console__title", "accessory__title", "collectable__title",
                     "description"]
    search_help_text = "Busca usando el titulo del videojuego, consola, accesorio, colleccionable o el codigo de barra"
    readonly_fields = [
        "location_image",
        "product_image",
        "id",
        "creation_date",
        "modification_date",
        "payment_link"
    ]
    exclude = ('remaining', 'payment', 'group')
    list_per_page = 50
    honeypot_fields = ['amount_to_notify', 'type', 'order', 'payment_link', 'remaining',
                       'provider_purchase_date', 'region', 'remaining', 'order']

    change_form_template = "overrides/change_form.html"
    change_list_template = "overrides/change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Get the groups the user belongs to
        user_groups = request.user.groups.all()

        # If the user is an All Access user, show all products
        if request.user.groups.filter(name="All Access"):
            return qs

        # Otherwise, filter products by the groups the user belongs to
        return qs.filter(group__in=user_groups)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            query = Q()
            for business_name in settings.BUSINESSES:
                query |= Q(name=business_name)

            user_groups = request.user.groups.filter(query)
            if user_groups.exists():
                # Each product should have a business group assigned to it (The business owner)
                obj.group = user_groups.first()

        if "image" in form.changed_data:
            new_img = form.cleaned_data['image']
            obj.image = None if not new_img else new_img
            obj.save()

            adi_copies = obj.equal_products()
            if type(adi_copies) is not str and adi_copies:
                copies_pk = [adi.product.pk for adi in adi_copies]

                Product.objects.filter(pk__in=copies_pk).update(image=obj.image)
            return

        obj.updated_by_admin = True
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not request.user.is_superuser:
            for field in self.honeypot_fields:
                if form.base_fields.get(field):
                    form.base_fields[field].widget = forms.HiddenInput()
        if not obj:
            form.base_fields['state'].widget = forms.HiddenInput()

        return form

    def set_location(self, request, queryset):
        new_location = queryset.filter(location__isnull=False).first()

        if new_location:
            queryset.update(location=new_location.location)

            self.message_user(request, f"Se actualizó el location de {queryset.count()} objetos correctamente.")
        else:
            self.message_user(request, "No hay objetos relacionados con una ubicación definida.", level='warning')

    set_location.short_description = "Actualizar location con el primer objeto relacionado"

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, "")
        if search_term:
            options_dict = defaultdict(list)

            for product in queryset:
                key = unidecode(product.description.lower())
                options_dict[key].append(product.description)

            search_query_lower = unidecode(search_term.lower())
            filtered_results = [desc for key, descs in options_dict.items() if search_query_lower in key for desc in
                                descs]

            queryset = queryset.filter(
                Q(videogame__title__icontains=search_term) | Q(barcode__exact=search_term) |
                Q(console__title__icontains=search_term) | Q(accessory__title__icontains=search_term) |
                Q(collectable__title__icontains=search_term) | Q(description__in=filtered_results))

            # queryset = exclude_copies(queryset)
        return queryset, use_distinct

    def used_display(self, obj):
        color = 'orange' if obj.used else 'blue'
        value = "usado" if obj.used else "nuevo"
        style = 'color: {}; border: 1px solid {}; padding: 4px; border-radius: 4px;'.format(color, color)

        return format_html('<span style="{}">{}</span>', style, value)

    used_display.short_description = 'Used'

    class Media:
        css = {
            'all': ('css/admin_styles.css',)
        }
        js = ('js/admin_scripts.js',)

    def product_image(self, obj):
        return format_html('<img src="{}" width="50" height="50" />', obj.image.url)

    product_image.short_description = 'Product Image'

    def location_image(self, obj):
        if not obj.location: return
        return format_html('<img src="{}" width="100" height="100" />', obj.location.location_image.url)

    location_image.short_description = 'Location Image'

    def get_exclude(self, request, obj=None):
        exclude = list(self.exclude)

        if obj:
            exclude.remove('remaining')

        if request.user.groups.filter(name="All Access"):
            exclude.remove("group")

        return exclude

    def payment_link(self, obj):
        if obj.payment:
            link = format_html(
                f'<a href="/admin/product/payment/{obj.payment.id}/change/">{obj.payment}</a>'
            )
            return link
        else:
            return "N/A"

    def tipo(self, obj):
        try:
            return obj.get_product_type()
        except:
            return "ERROR no tiene tipo de producto"

    def _state(self, obj: Product):
        hex_colors = {
            StateEnum.available: "#70BF2B",
            StateEnum.sold: "#E70012",
            StateEnum.reserved: "#FCC10F",
            StateEnum.pending: "#DC3545"
        }
        return format_html(
            "<div style='padding: 0.5em; background-color: {}; color: #fff; border-radius: 0.25em;'>{}</div>",
            hex_colors[obj.state],
            obj.get_state_display()
        )

    def get_inlines(self, request, obj):

        if request.user.groups.filter(name="All Access").exists():
            return [VideoGamesInline, ConsoleInline, AccessoryInline, CollectableInline, ReplacementsInline, FoodInline]
        elif request.user.groups.filter(name="Store").exists():
            return [VideoGamesInline, ConsoleInline, AccessoryInline, CollectableInline, ReplacementsInline]
        elif request.user.groups.filter(name="Restaurant").exists():
            return [FoodInline]

    def etiquetas(self, obj: Product):
        styling = lambda color: "display: inline-block; padding: 0.5em; " \
                                f"background-color: {color}; color: #fff; border-radius: 0.25em;"
        tag = lambda name, color: f'<div style="{styling(color)}">{name}</div>'

        inner_tags = "".join([tag(t.name, t.color) for t in obj.tags.all()])
        html = f"<div id='product_tags'>{inner_tags}</div>",

        return mark_safe(html[0])

    etiquetas.short_description = "Etiquetas"

    def get_readonly_fields(self, request, obj: Product = None):
        readonly_fields = list(self.readonly_fields)  # Start with initial readonly_fields

        if obj:
            if obj.state == StateEnum.sold:
                readonly_fields.extend(
                    ['amount', 'sale_price', 'remaining', 'barcode', 'provider_purchase_date', 'sale_date'])
            elif obj.state == StateEnum.reserved:
                readonly_fields.extend(
                    ['sale_price', 'remaining', 'barcode', 'provider_purchase_date', 'sale_date', 'amount'])
            elif obj.state == StateEnum.available:
                readonly_fields.extend(['remaining', 'provider_purchase_date', 'sale_date'])

        if (not obj or not obj.location) and 'location_image' in readonly_fields:
            readonly_fields.remove('location_image')
        if (not obj or not obj.image) and 'image' in readonly_fields:
            readonly_fields.remove('image')
        if (not obj or obj.payment.payment_method == PaymentMethodEnum.na) and 'payment_link' in readonly_fields:
            readonly_fields.remove('payment_link')

        return readonly_fields

    def response_change(self, request, obj: Product):
        if "_print_barcode" in request.POST:
            messages.add_message(request, messages.INFO, f"Descarga exitosa de la barra de codigo")
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="barcode_with_string.pdf"'

            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)

            data_string = str(obj.barcode)  # Customize this to extract the string data from your model
            c.drawString(10, 750, str(obj))
            c.drawString(30, 730, obj.barcode)

            barcode = code128.Code128(data_string, barWidth=1, barHeight=25)
            barcode.drawOn(c, 0, 700)

            c.showPage()

            c.save()
            pdf_data = buffer.getvalue()
            buffer.close()

            response.write(pdf_data)
            return response
        return super().response_change(request, obj)

    payment_link.allow_tags = True
    tipo.short_description = 'Tipo de producto'


class ConsoleAdmin(admin.ModelAdmin):
    model = Console


class CollectableAdmin(admin.ModelAdmin):
    model = Collectable


class VideoGameAdmin(admin.ModelAdmin):
    model = VideoGame
    list_display = ["title", "console", "get_region"]
    list_filter = ("console", "product__region")
    search_fields = ["title"]

    @admin.display(description='Region')
    def get_region(self, obj):
        return obj.product.region


class ReplacementAdmin(admin.ModelAdmin):
    model = Replacement
    list_display = ["title", "console"]
    list_filter = ("console", "product__region")
    search_fields = ["title"]


class AccessoryAdmin(admin.ModelAdmin):
    model = Accessory


class PaymentAdmin(admin.ModelAdmin):
    model = Payment


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0
    form = SaleInlineForm


class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'display_day', 'date', 'display_total', 'display_total_business', 'display_total_mauricio',
        'display_total_joseph', 'display_total_consignment')
    ordering = ("-date",)
    inlines = [SaleInline]
    readonly_fields = ("total",)
    list_filter = (WeekdayFilter,)

    @admin.display(description='Total', ordering='total')
    def display_total(self, obj):
        return obj.calculate_total()

    display_total.short_description = 'Total'

    @admin.display(description='Total Business', ordering='total_business')
    def display_total_business(self, obj):
        return obj.calculated_total_business

    @admin.display(description='Total Mauricio', ordering='total_mauricio')
    def display_total_mauricio(self, obj):
        return obj.calculated_total_mauricio

    @admin.display(description='Total Joseph', ordering='total_joseph')
    def display_total_joseph(self, obj):
        return obj.calculated_total_joseph

    @admin.display(description='Total Consignacion', ordering='total_consignacion')
    def display_total_consignment(self, obj):
        return obj.calculated_total_consignment

    def display_day(self, obj: Report):
        return calendar.day_name[obj.date.weekday()]

    display_day.short_description = 'Day of week'


class SaleAdmin(admin.ModelAdmin):
    model = Sale
    form = SaleAdminForm

    exclude = (
        'products',
        'customer_mail',
        'customer_name',
    )
    readonly_fields = (
        'creation_date_time',
        'receipt_products',
        'onvo_pay_payment_intent_id',
        'client'
    )
    list_display = ("__str__", "client_link", "type", "platform", "creation_date_time")
    search_fields = ("customer_name", "customer_mail", "products__videogame__title", "payment_details",
                     "products__console__title", "products__accessory__title", "products__collectable__title")
    list_filter = (UserSalesFilter, "type", PaymentPendingFilter, ToBeShippedFilter, "shipping", "platform")
    ordering = ("-creation_date_time",)

    change_form_template = "overrides/btn_sale.html"

    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:administration_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client)
        return "-"

    client_link.admin_order_field = 'client'  # Allows sorting by client
    client_link.short_description = 'Client'  # Column name in admin

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            sale = self.get_object(request, object_id)
            extra_context['sale'] = sale
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        """Include a download link for voucher when one exists."""
        fields = list(self.readonly_fields)
        if obj and getattr(obj, 'voucher', None):
            fields.append('voucher_link')
        return fields

    def get_exclude(self, request, obj=None):
        """Exclude the editable `voucher` field when a voucher is already set so only the link shows."""
        exclude = list(self.exclude) if self.exclude else []
        if obj and getattr(obj, 'voucher', None):
            if 'voucher' not in exclude:
                exclude.append('voucher')
        return tuple(exclude)

    def voucher_link(self, obj: Sale):
        if not obj.voucher:
            return "N/A"
        try:
            url = obj.voucher.url
        except Exception:
            return "N/A"
        return format_html('<a href="{}" target="_blank">Download voucher</a>', url)

    voucher_link.short_description = 'Voucher'

    def format_product_string(self, product: Product):
        product_url = reverse('admin:product_product_change', args=[product.pk])
        net_price = product.payment.net_price if product.payment else product.sale_price
        owner = product.owner
        console_type = product.console_type
        product_string = (f"<li style='list-style: disc;'>{str(product)} - {console_type} - ₡{net_price} - {owner} - ID: "
                          f"<a href='{product_url}'>{product.pk}</a> </li>\n")
        return mark_safe(product_string)

    def receipt_products(self, obj: Sale):
        products_string = [self.format_product_string(product) for product in obj.products.all()]
        return mark_safe(f'<ul style="margin-left: 0; padding-left: 0;">{"".join(products_string)}</ul>')

    def response_change(self, request, obj: Sale):
        if "_confirm_payment" in request.POST:
            # Ensure the sale has a payment intent ID
            payment_intent_id = obj.onvo_pay_payment_intent_id
            if not payment_intent_id:
                self.message_user(request, "No Payment Intent ID found on this sale.", level=messages.ERROR)
                return super().response_change(request, obj)

            headers = {"Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"}
            capture_url = f"https://api.onvopay.com/v1/payment-intents/{payment_intent_id}/capture"


            try:
                print("Making capture for:", payment_intent_id)
                capture_response = requests.post(capture_url, headers=headers)
                capture_response.raise_for_status()
            except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as err:
                self.message_user(request, f"Error intentando de confirmar pago: {err}", level=messages.ERROR)
                return HttpResponseRedirect(request.path)

            context = {"payment_details": obj.payment_details, "items": obj.products.all()}

            rendered_template = render_to_string("online-payments/capture-payment.html", context)

            try:
                GenerateBill.enviar_factura_por_correo(
                    rendered_template,
                    obj.customer_mail,
                    0
                )
            except SendMailError as e:
                self.message_user(f'Error al enviar el correo: {e}', level=messages.ERROR)
                return HttpResponseRedirect(request.path)

            obj.type = SaleTypeEnum.Purchase
            today = datetime.datetime.today().date()
            obj.report, _ = Report.objects.get_or_create(date=today)
            obj.save()
            print("Updated sale: ", obj)

            for product in obj.products.all():
                product.state = StateEnum.sold
                product.save()
                print("Updated product: ", product)

            self.message_user(request, f"El pago #{obj.pk} por ₡{obj.gross_total} fue hecho con exito", level=messages.SUCCESS)
        elif "_cancel_payment" in request.POST:
            # Ensure the sale has a payment intent ID
            payment_intent_id = obj.onvo_pay_payment_intent_id
            if not payment_intent_id:
                self.message_user(request, "No Payment Intent ID found on this sale.", level=messages.ERROR)
                return super().response_change(request, obj)

            headers = {"Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"}
            capture_url = f"https://api.onvopay.com/v1/payment-intents/{payment_intent_id}/cancel"

            try:
                print("Making cancel for:", payment_intent_id)
                capture_response = requests.post(capture_url, headers=headers)
                capture_response.raise_for_status()
            except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as err:
                self.message_user(request, f"Error intentando de cancelar pago: {err}", level=messages.ERROR)
                return HttpResponseRedirect(request.path)

            context = {"payment_details": obj.payment_details, "items": obj.products.all()}

            rendered_template = render_to_string("online-payments/cancel-payment.html", context)

            try:
                GenerateBill.enviar_factura_por_correo(
                    rendered_template,
                    obj.customer_mail,
                    0
                )
            except SendMailError as e:
                self.message_user(f'Error al enviar el correo: {e}', level=messages.ERROR)
                return HttpResponseRedirect(request.path)

            obj.type = SaleTypeEnum.Cancelled
            today = datetime.datetime.today().date()
            obj.report, _ = Report.objects.get_or_create(date=today)
            obj.save()
            print("Updated sale: ", obj)

            for product in obj.products.all():
                product.state = StateEnum.available
                product.save()
                print("Updated product: ", product)

            self.message_user(request, f"El pago #{obj.pk} por ₡{obj.gross_total} fue cancelado con exito",
                              level=messages.WARNING)

        elif "_print_receipt" in request.POST:
            context = {'store_name': business_information["store_name"],
                       'store_address': business_information["store_address"],
                       'store_contact': business_information["store_contact"],
                       'store_mail': business_information["store_mail"],
                       'receipt_number': "", 'purchase_date': obj.purchase_date_time,
                       'customer_name': obj.customer_name, 'customer_mail': obj.customer_mail,
                       'payment_method': obj.payment_method,
                       'payment_details': obj.payment_details,
                       'receipt_comments': obj.receipt_comments,
                       'return_policy': qrOptions[1], 'qr_url': qrLinkOptions[1],
                       "discounts": formatted_number(obj.discount), "total_amount": formatted_number(obj.gross_total)
                       }

            items = []
            if obj.type == SaleTypeEnum.Repair:
                formatted_price = formatted_number(obj.gross_total)
                items.append({
                    'id': "S",
                    'name': "---Reparaciòn---",
                    'price': formatted_price
                })
            else:
                product = obj.products.all()[0]
                if product.state == StateEnum.reserved:
                    items.append({
                        'id': product.id,
                        'name': product.__str__(),
                        'price': formatted_number(product.payment.sale_price - product.payment.remaining),
                        'status': "APARTADO"
                    })

                    items_remaining = [{
                        'id': product.id,
                        'name': product.__str__(),
                        'remaining': formatted_number(product.payment.remaining)
                    }]

                    context['items_remaining'] = items_remaining
                else:
                    for item in obj.products.all():
                        formatted_price = formatted_number(item.payment.sale_price)
                        items.append({
                            'id': item.id,
                            'name': item.__str__(),
                            'price': formatted_price
                        })

            context['items'] = items
            context['subtotal'] = formatted_number(obj.subtotal)
            if float(obj.taxes):
                context['taxes'] = formatted_number(obj.taxes)
            else:
                context['taxes'] = 0
            rendered_template = render_to_string("receipt-template.html", context)

            response = HttpResponse(rendered_template, content_type='text/html')

            response['Content-Disposition'] = 'inline; filename="bill.html"'
            response['Cache-Control'] = 'no-cache'
            admin_url = f"https://readygamescr.com/admin/product/sale/{obj.id}/change/"
            js_script = f"""
                <form action="{admin_url}" method="GET" id="openAdminForm">
                    <input type="submit" style="display:none;">
                </form>
                <script type="text/javascript">
                    document.getElementById('openAdminForm').submit();
                    window.print()
                </script>
            """
            response.content = response.content.decode('utf-8').replace('</body>', js_script + '</body>').encode(
                'utf-8')
            return response

        return super().response_change(request, obj)


class LogAdmin(admin.ModelAdmin):
    model = Log


class ExpenseAdmin(admin.ModelAdmin):
    model = Expense


class TagAdmin(admin.ModelAdmin):
    model = Tag


admin_site.register(Product, ProductAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Expense, ExpenseAdmin)
admin_site.register(Report, ReportAdmin)
admin_site.register(Sale, SaleAdmin)
admin_site.register(Log, LogAdmin)
admin_site.register(Payment, PaymentAdmin)

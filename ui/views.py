import json

import logging
from datetime import datetime
from openpyxl import Workbook

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from helpers.payment import formatted_number, choices_payment
from helpers.qr import qrOptions, qrLinkOptions
from helpers.returnPolicy import return_policy_options
from django.db import transaction
from product.models import Product, StateEnum, Sale, Report, OwnerEnum
from rest_framework.views import APIView
from rest_framework.response import Response


class ReturnPolicyView(TemplateView):
    template_name = "return-policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        t_param = kwargs.get('t')
        context['return_policy_text'] = return_policy_options[int(t_param)]["desc"]
        return context


class CountDownView(TemplateView):
    template_name = "coming-soon.html"


class ReceiptView(TemplateView):
    template_name = "receipt.html"


class ReportView(TemplateView):
    template_name = "report.html"


class GenerateBill(TemplateView):
    template_name = "receipt-template.html"

    SERVICE = "S"

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode('utf-8'))
        context = self.get_context_data(**kwargs)
        context['store_name'] = data['storeName']
        context['store_address'] = data['storeAddress']
        context['store_contact'] = data['storeContact']
        context['store_mail'] = data['storeMail']
        context['receipt_number'] = data['receiptNumber']
        context['purchase_date'] = data['purchaseDate']
        context['customer_name'] = data['customerName']
        context['customer_mail'] = data['customerMail']
        context['payment_method'] = data['paymentMethod']
        context['items'] = data['items']
        context['payment_details'] = data['paymentDetails']
        context['return_policy'] = qrOptions[data['returnPolicy']]
        context['qr_url'] = qrLinkOptions[data['returnPolicy']]
        items = []
        items_remaining = []
        for item in data['items']:
            formatted_price = formatted_number(item['price'])  # rework por
            # la nueva tabla
            items.append({
                'id': item['id'],
                'name': item['name'],
                'price': formatted_price,
                'status': "APARTADO" if item.get('reserved') else ""
            })
            if item['id'] != self.SERVICE:
                product = Product.objects.get(id=item['id'])
                product.sale_date = datetime.now()
                payment = product.payment
                reserved = item.get('reserved')
                if payment.remaining == payment.sale_price:  # al iniciar un pago con un producto, se le
                    # setea el metodo de pago y el costo nuevo si es el caso
                    pay = choices_payment(data['paymentMethod'], payment.sale_price)
                    payment.payment_method = pay["method"]
                    payment.sale_price = pay["price"]
                    payment.remaining = pay["price"]
                payment.remaining = max(0, payment.remaining - int(item['price']) if reserved else 0)
                if payment.remaining:
                    items_remaining.append({
                        'id': item['id'],
                        'name': item['name'],
                        'remaining': formatted_number(payment.remaining)
                    }
                    )
                product.state = StateEnum.sold if not reserved or product.remaining <= 0 else StateEnum.reserved
                payment.save()
                product.save()
        context['items_remaining'] = items_remaining
        context['items'] = items
        context['subtotal'] = formatted_number(data['subtotal'])
        if float(data['taxes']):
            context['taxes'] = formatted_number(data['taxes'])
        else:
            context['taxes'] = 0
        context['discounts'] = formatted_number(data['discounts'])
        context['total_amount'] = formatted_number(data['totalAmount'])

        rendered_template = render_to_string(self.template_name, context)

        response = HttpResponse(rendered_template, content_type='text/html')

        self.create_sale(data)

        try:
            self.enviar_factura_por_correo(rendered_template, data['customerMail'], data['returnPolicy'])
        except SendMailError as e:
            logging.error(f'Error al enviar el correo: {e}')

        response['Content-Disposition'] = 'inline; filename="bill.html"'
        response['Cache-Control'] = 'no-cache'
        return self.render_to_response(context)

    def create_sale(self, data):
        with transaction.atomic():
            today = datetime.today().date()
            report, created = Report.objects.get_or_create(date=today)
            warranty_type = return_policy_options[data['returnPolicy']]["name"]

            sale = Sale.objects.create(
                report=report,
                warranty_type=warranty_type,
                purchase_date_time=data['purchaseDate'],
                payment_method=data['paymentMethod'],
                subtotal=data['subtotal'],
                discount=data['discounts'],
                taxes=data['taxes'],
                total=data['totalAmount'],
                payment_details=data['paymentDetails'],
                customer_name=data['customerName'],
                customer_mail=data['customerMail'],
            )

            for item in data['items']:
                product_id = item['id']
                if product_id != self.SERVICE:
                    product = Product.objects.get(id=product_id)
                    sale.products.add(product)

            return sale

    def enviar_factura_por_correo(self, factura_html, address, return_policy):
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_user = 'readygamescr@gmail.com'
        smtp_password = 'dasieujszfbbvcew'

        remittent = 'readygamescr@gmail.com'
        destination = address

        message = MIMEMultipart()
        message['From'] = remittent
        message['To'] = f'{destination}'
        message['Subject'] = '¡Factura Ready Games🎮🕹️👾!'

        email_template_name = "return-policy.html"
        email_context = {
            'return_policy_text': return_policy_options[return_policy]["desc"],
        }

        rendered_email_template = render_to_string(email_template_name, email_context)

        message.attach(MIMEText(factura_html, 'html'))
        message.attach(MIMEText(rendered_email_template, 'html'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(remittent, destination, message.as_string())
            print('Correo enviado correctamente')
        except Exception as e:
            raise SendMailError(str(e))
        finally:
            server.quit()


class CalculateTotalView(APIView):
    def post(self, request, format=None):
        data = request.data
        products_data = data.get('products', [])
        tax = data.get('tax', False)
        total = 0
        tax_total = 0
        sub_total = 0
        for product_data in products_data:
            price = float(product_data.get('price', 0))
            remaining = product_data.get('remaining', False)

            if remaining:
                total += price
                sub_total += price
                if tax:
                    tax_total += price * 0.13
                    sub_total -= tax_total
                break
            else:
                sub_total += price
                if tax:
                    taxed_price = price / 0.87
                    total += taxed_price
                    tax_total += taxed_price - price
                else:
                    total += price

        response_data = {
            'subtotal': round(sub_total, 2),
            'tax': round(tax_total, 2),
            'total': round(total, 2),
        }

        return Response(response_data)


def generate_excel_report(request, fecha=None):
    if fecha:
        try:
            datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            fecha = datetime.today().strftime('%Y-%m-%d')
    else:
        fecha = datetime.today().strftime('%Y-%m-%d')

    today = fecha
    report = Report.objects.get_or_create(date=today)[0]
    sales = Sale.objects.filter(report=report)

    wb = Workbook()
    ws = wb.active

    ws.append(['Producto', 'Precio Vendido', "Total Tienda", "Recibido", "Faltante", "Dueño"])

    total_sales = 0.0
    total_tienda = 0.0
    total_remaining = 0.0

    for sale in sales:
        for product in sale.products.all():
            receive_price = product.sale_price
            remaining = 0
            if product.state == StateEnum.reserved:
                remaining = product.remaining
                receive_price = receive_price - remaining

            if product.owner == OwnerEnum.Business:
                parte_tienda = float(receive_price)
            else:
                parte_tienda = float(receive_price // 10)
            total_remaining += float(remaining)
            total_tienda += parte_tienda
            ws.append([product.__str__(), product.sale_price, parte_tienda, receive_price, remaining, product.owner])
        total_sales += float(sale.total)

    ws.append(['Total de Ventas', total_sales, total_tienda, "--", total_remaining])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=reporte_{today}.xlsx'
    wb.save(response)

    return response


class SendMailError(Exception):
    pass

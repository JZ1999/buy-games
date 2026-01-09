from babel.numbers import format_currency
import decimal
from django.db import models


class PaymentMethodEnum(models.TextChoices):
    tasa = "tasa 0", "T0"
    card = "card", "Card"
    cash = "cash", "Cash"
    sinpe = "sinpe", "Sinpe"
    na = "na", "N/A"


def factor_tasa_0():
    return 0.77


def factor_tasa_0_10_months():
    return 0.60


def factor_card():
    return 0.84


def commission_price(price, factor):
    return roundup_nearest_hundred(int(price) / decimal.Decimal(factor))


def roundup_nearest_hundred(x):
    return round(x if x % 100 == 0 else x + 100 - x % 100, 2)


def is_numeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def formatted_number(number: float | decimal.Decimal | int | str):
    if type(number) is str and not is_numeric(number):
        return ''
    elif type(number) not in [float, int, decimal.Decimal]:
        return ''
    return str(format_currency(number, 'CRC', locale='es_CR'))


def choices_payment(method, price):
    payment = {
        "Credit Card/Debit Card": {
            "method": PaymentMethodEnum.card,
            "price": commission_price(price, factor_card())
        },
        "Sinpe": {
            "method": PaymentMethodEnum.cash,
            "price": price
        },
        "Cash": {
            "method": PaymentMethodEnum.cash,
            "price": price
        },
        "Transfer": {
            "method": PaymentMethodEnum.cash,
            "price": price
        },
        "Tasa 0": {
            "method": PaymentMethodEnum.tasa,
            "price": commission_price(price, factor_tasa_0())
        },
    }

    return payment[method]

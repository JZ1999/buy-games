from django.contrib import admin
from django.db.models import Q, F
from product.models import ConsoleEnum, StateEnum


class ConsoleTitleFilter(admin.SimpleListFilter):
    title = 'Console Title'  # Displayed filter title
    parameter_name = 'console_title'  # URL parameter name for the filter

    def lookups(self, request, model_admin):
        # Return a list of tuples representing the filter options
        # The first element in each tuple is the actual value to filter on,
        # and the second element is the human-readable option name
        return ConsoleEnum.choices

    def queryset(self, request, queryset):
        # Apply the filter to the queryset
        value = self.value()
        if value:
            return queryset.filter(Q(console__title=value) | Q(videogame__console=value) | Q(accessory__console=value))
        return queryset


class TypeFilter(admin.SimpleListFilter):
    title = 'Tipo'
    parameter_name = 'tipo'

    def lookups(self, request, model_admin):
        return (
            ('videogame', 'Videojuego'),
            ('console', 'Consola'),
            ('accessory', 'Accesorio'),
            ('collectable', 'Coleccionable'),
        )

    def queryset(self, request, queryset):
        return self.get_products_by_type(self.value(), queryset)


    @staticmethod
    def get_products_by_type(product_type: str, queryset):
        if product_type == 'videogame':
            return queryset.filter(videogame__isnull=False)
        elif product_type == 'console':
            return queryset.filter(console__isnull=False)
        elif product_type == 'accessory':
            return queryset.filter(accessory__isnull=False)
        elif product_type == 'collectable':
            return queryset.filter(collectable__isnull=False)

class DuplicatesFilter(admin.SimpleListFilter):
    title = 'Mostrar duplicados'
    parameter_name = 'duplicates'

    def lookups(self, request, model_admin):
        # Devuelve las opciones de filtro y sus etiquetas
        return (
            ('yes', ('Si')),
            ('no', ('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(hidden=False)
        else:
            return queryset


class SoldFilter(admin.SimpleListFilter):
    title = 'Estado de Producto'
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        # Devuelve las opciones de filtro y sus etiquetas
        return (
            ('vendido', ('Vendido')),
            ('available', ('Disponible')),
            ('reserved', ('Apartado')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'vendido':
            return queryset.filter(state=StateEnum.sold)
        elif self.value() == 'available':
            return queryset.filter(state=StateEnum.available)
        elif self.value() == 'reserved':
            return queryset.filter(state=StateEnum.reserved)
        else:
            return queryset.filter(Q(state=StateEnum.available) | Q(state=StateEnum.reserved))


class BelowThreshHoldFilter(admin.SimpleListFilter):
    title = 'Bajo el limite de Productos'
    parameter_name = 'notify'

    def lookups(self, request, model_admin):
        # Devuelve las opciones de filtro y sus etiquetas
        return (
            ('to_notify', 'A Notificar'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'to_notify':
            all_products = queryset.all()
            filtered_products = [product.id for product in all_products if product.amount_to_notify and  product.amount_to_notify >= product.copies]
            return all_products.filter(id__in=filtered_products)
        return queryset.all()

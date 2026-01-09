from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from rest_framework.routers import DefaultRouter

from product.views import ProductViewSet, CollectableViewSet, VideoGameViewSet, AccessoryViewSet, ReportViewSet, \
    DailySalesReport, GenerateExcelOfProducts, GenerateImageOfProducts, ProductStateView
from product.views import Consoles

router = DefaultRouter()
router.register(r'reports', ReportViewSet)

urlpatterns = [
    path("products/excel", GenerateExcelOfProducts.as_view(), name="products-excel"),
    path("products/image", GenerateImageOfProducts.as_view(), name="products-image"),
    path("products/", ProductViewSet.as_view({"post": "create", "get": "list"})),
    path('products/state/', ProductStateView.as_view(), name='products-states'),
    path("product/<str:pk>/", ProductViewSet.as_view({"get": "retrieve"})),
    path("collectable/", CollectableViewSet.as_view({"post": "create", "get": "list"})),
    path("video-game/", VideoGameViewSet.as_view({"post": "create", "get": "list"})),
    path("accessory/", AccessoryViewSet.as_view({"post": "create", "get": "list"})),
    path('sales/', DailySalesReport.as_view(), name='daily-sales-report'),
    path('consoles/', Consoles.as_view(), name='consoles-list'),

]
urlpatterns += router.urls

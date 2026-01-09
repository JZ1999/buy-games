from django.urls import path

from rest_framework.routers import DefaultRouter

from administration.views import CouponViewSet, ClientViewSet, CreatePaymentIntent, CreateCustomer, CreatePaymentMethod, ConfirmPaymentIntent, NewsViewSet

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = [
    path("coupon/<str:code>/", CouponViewSet.as_view({"get": "retrieve"})),
    path("client/<str:email>/", ClientViewSet.as_view({"get": "retrieve"})),
    path("clients/", ClientViewSet.as_view({"post": "list_of_clients"})),
    
    path('create-payment-intent', CreatePaymentIntent.as_view(), name='create-payment-intent'),
    path('create-customer', CreateCustomer.as_view(), name='create-customer'),
    path('create-payment-method', CreatePaymentMethod.as_view(), name='create-payment-method'),
    path('confirm-payment-intent', ConfirmPaymentIntent.as_view(), name='confirm-payment-intent'),
]
urlpatterns += router.urls

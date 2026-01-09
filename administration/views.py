import datetime

from django.db.models import Value, CharField, F
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from administration.models import Coupon, Client, Setting, News
from administration.serializer import CouponSerializer, ClientSerializer, NewsSerializer
from product.views import Throttling

import requests
from rest_framework.views import APIView
from rest_framework import status, viewsets
from django.conf import settings

class CouponViewSet(viewsets.ModelViewSet, Throttling):
    queryset = Coupon.objects.filter(expiration__gt=datetime.datetime.now())
    serializer_class = CouponSerializer
    permission_classes = []
    lookup_field = "code"


class ClientViewSet(viewsets.ModelViewSet, Throttling):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = []
    lookup_field = "email"

    @action(detail=False, methods=['post'])
    def list_of_clients(self, request, *args, **kwargs):
        clients = self.queryset.filter(email__icontains=request.data.get("email"))
        clients_serialized = self.serializer_class(
                clients,
                many=True
            )

        return Response(
            clients_serialized.data
        )
        
class CreateCustomer(APIView):
    def post(self, request, *args, **kwargs):
        if Setting.objects.first().disable_online_purchase:
            return JsonResponse(
                {"error": "Hubo un error con el sistema y no se hizo el cobro."},
                status=403
            )
        payload = {
            "name": request.data.get("name"),
            "email": request.data.get("email"),
            "description": request.data.get("description")
        }
        headers = {"Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"}

        try:
            response = requests.post('https://api.onvopay.com/v1/customers', json=payload, headers=headers)
            response.raise_for_status()
            return Response({"customerData": response.json()}, status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as err:
            return Response({"error": str(err)}, status=err.response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CreatePaymentMethod(APIView):
    def post(self, request, *args, **kwargs):
        if Setting.objects.first().disable_online_purchase:
            return JsonResponse(
                {"error": "Hubo un error con el sistema y no se hizo el cobro."},
                status=403
            )
        payload = {
            "type": "card",
            "card": {
                "number": request.data.get("number"),
                "expMonth": request.data.get("expMonth"),
                "expYear": request.data.get("expYear"),
                "cvv": request.data.get("cvv"),
                "holderName": request.data.get("holderName")
            }
            # "customerId": request.data.get("customerId")
        }
        headers = {"Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"}

        try:
            response = requests.post('https://api.onvopay.com/v1/payment-methods', json=payload, headers=headers)
            response.raise_for_status()
            return Response({"paymentMethod": response.json()}, status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as err:
            print(err)
            return Response({"error": str(err)}, status=err.response.status_code)
        except requests.exceptions.RequestException as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CreatePaymentIntent(APIView):
    def post(self, request, *args, **kwargs):
        if Setting.objects.first().disable_online_purchase:
            return JsonResponse(
                {"error": "Hubo un error con el sistema y no se hizo el cobro."},
                status=403
            )
        payload = {
            "captureMethod": "manual",
            "amount": request.data.get("amount"),
            "currency": request.data.get("currency"),
            # "customerId": request.data.get("customerId"),
            "description": request.data.get("description"),
            "metadata":{
                "userId":request.data.get("id"),
                "phoneNumber":request.data.get("phone"),
                "userName":request.data.get("name"),
                "userEmail":request.data.get("email")
            }
        }
        headers = {"Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"}

        try:
            response = requests.post('https://api.onvopay.com/v1/payment-intents', json=payload, headers=headers)
            response.raise_for_status()
            return Response({"paymentIntent": response.json()}, status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as err:
            print(err.response.json())
            return Response({"error": str(err)}, status=err.response.status_code)
        except requests.exceptions.RequestException as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ConfirmPaymentIntent(APIView):
    def post(self, request, *args, **kwargs):
        if Setting.objects.first().disable_online_purchase:
            return JsonResponse(
                {"error": "Hubo un error con el sistema y no se hizo el cobro."},
                status=403
            )
        paymentIntentId = request.data.get("paymentIntentId")
        paymentMethodId = request.data.get("paymentMethodId")

        if not paymentIntentId or not paymentMethodId:
            return Response({"error": "Payment Intent ID and Payment Method ID are required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"
        }

        try:
            response = requests.post(
                f'https://api.onvopay.com/v1/payment-intents/{paymentIntentId}/confirm',
                json={"paymentMethodId": paymentMethodId},
                headers=headers
            )
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as err:
            print(err)
            return Response({"error": str(err)}, status=err.response.status_code)
        except requests.exceptions.RequestException as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CapturePaymentIntent(APIView):
    def post(self, request, *args, **kwargs):
        payment_intent_id = request.data.get("paymentIntentId")

        if not payment_intent_id:
            return Response({"error": "Payment Intent ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.ONVOPAY_API_KEY}"
        }

        try:
            # Make the API call to capture the payment
            response = requests.post(
                f'https://api.onvopay.com/v1/payment-intents/{payment_intent_id}/capture',
                headers=headers
            )
            response.raise_for_status()

            # Return the response data
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as err:
            print(err)
            return Response({"error": str(err)}, status=err.response.status_code)
        except requests.exceptions.RequestException as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset that returns `initial` (up to 4 non-carousel items)
    and `carousel` items in the `list` action.
    """
    queryset = News.objects.filter(active=True)
    serializer_class = NewsSerializer
    permission_classes = []

    def list(self, request, *args, **kwargs):
        # Return up to 4 active news items ordered by creation date (most recent first)
        qs = self.queryset.order_by('-creation_date')[:4]
        data = self.get_serializer(qs, many=True, context={"request": request}).data
        return Response(data)

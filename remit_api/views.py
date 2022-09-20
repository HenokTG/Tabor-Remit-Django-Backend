import json
import requests

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView

from paypalrestsdk import notifications

from .models import (Transactions, Invoces, PackageOffers,
                     PromoCodes, Operators, PaymentMethod)
from agent_api.models import AgentProfile
from .serializers import (TransactionSerializer, InvoiceSerializer, PackageSerializer,
                          OperatorSerializer, PromoCodeSerializer)


class TransactionsAdminViewset(ModelViewSet):

    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]


class TransactionsListView(ListAPIView):

    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer


class InvoicesAdminViewset(ModelViewSet):

    queryset = Invoces.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminUser]


class InvoicesCreateView(CreateAPIView):

    queryset = Invoces.objects.all()
    serializer_class = InvoiceSerializer

    def post(self, request, *args, **kwargs):

        order_id = kwargs.get('order_id')

        phone = request.data["phoneNumber"]
        total = request.data["valueCharged"]
        airtime = request.data["airtimeValue"]
        package = PackageOffers.objects.get(
            id=request.data["packageID"])
        agent = AgentProfile.objects.get(
            agent_name=request.data["AgentCode"])
        operator = Operators.objects.get(
            id=request.data["operatorID"])
        method = PaymentMethod.objects.get(
            id=request.data["payMethodID"])

        try:
            promo = PromoCodes.objects.get(
                promo_code=request.data["promoCode"])
            promo_disc = promo.promo_discount_rate
        except PromoCodes.DoesNotExist:
            promo = None
            promo_disc = 0

        Check_Amount = package.selling_price_USD * (1 - package.discount_rate) * \
            (1-operator.operator_discount_rate) * (1-promo_disc)
       
        if Check_Amount == total:

            new_invoice = Invoces.objects.create(
                invoive_id=order_id,
                receiver_phone=phone,
                package_offers=package,
                agent=agent,
                promo_code=promo,
                operator=operator,
                payment_method=method)

            serializer = InvoiceSerializer(new_invoice)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"Error": "Sorry, suspected price manipulation."}, status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)


class PackagesViewSet(ModelViewSet):

    queryset = PackageOffers.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAdminUser]


class PackageLIstView(ListAPIView):

    queryset = PackageOffers.objects.all()
    serializer_class = PackageSerializer


class OperatorAdminViewSet(ModelViewSet):

    queryset = Operators.objects.all()
    serializer_class = OperatorSerializer
    permission_classes = [IsAdminUser]


class OperatorLIstView(ListAPIView):

    queryset = Operators.objects.all()
    serializer_class = OperatorSerializer


class PromoCodeRetrieveView(RetrieveAPIView):

    queryset = PromoCodes.objects.all()

    def get(self, request, **kwargs):
        code = kwargs.get('promo_code')
        try:
            promocode = PromoCodeSerializer(PromoCodes.objects.get(
                promo_code=code))
            return Response(promocode.data)
        except PromoCodes.DoesNotExist:
            return Response({"message": "Submited promocode is invalid."}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name="dispatch")
class RemitProcessWebhookView(View):
    def post(self, request):
        if "HTTP_PAYPAL_TRANSMISSION_ID" not in request.META:
            return HttpResponseBadRequest()

        auth_algo = request.META['HTTP_PAYPAL_AUTH_ALGO']
        cert_url = request.META['HTTP_PAYPAL_CERT_URL']
        transmission_id = request.META['HTTP_PAYPAL_TRANSMISSION_ID']
        transmission_sig = request.META['HTTP_PAYPAL_TRANSMISSION_SIG']
        transmission_time = request.META['HTTP_PAYPAL_TRANSMISSION_TIME']
        webhook_id = settings.PAYPAL_WEBHOOK_ID
        event_body = request.body.decode(request.encoding or "utf-8")

        valid = notifications.WebhookEvent.verify(
            transmission_id=transmission_id,
            timestamp=transmission_time,
            webhook_id=webhook_id,
            event_body=event_body,
            cert_url=cert_url,
            actual_sig=transmission_sig,
            auth_algo=auth_algo,
        )

        if not valid:
            return HttpResponseBadRequest()

        webhook_event = json.loads(event_body)

        event_type = webhook_event["event_type"]
        event_detail = webhook_event["resource"]

        CHECKOUT_ORDER_APPROVED = "CHECKOUT.ORDER.APPROVED"

        if event_type == CHECKOUT_ORDER_APPROVED:

            # print(json.dumps(event_detail, indent=4))
            process_card_purchase(event_detail, event_type)

        return HttpResponse()


def process_card_purchase(event_detail):

    order_id = event_detail["id"]
    order_amount = event_detail["purchase_units"][0]["amount"]["value"]
    customer_name = event_detail["payer"]["name"]["given_name"]
    customer_email = event_detail["payer"]["email_address"]
    Transaction_detail = Transactions.objects.get(
        transaction_id=order_id)

    if Transaction_detail.transaction_amount == float(order_amount):
        print("Payment Verified. Continue card purchase.")
        
        phone_number = Transaction_detail.invoice.receiver_phone
        airtime_amount = Transaction_detail.airtime_amount
        service_provider = Transaction_detail.invoice.operator.operator_name
        data = {'phone': phone_number,
                'value': airtime_amount,
                }  # This may not be the actual key-value pair
        API_ENDPOINT = 'https://httpbin.org/post'  # Card purchase API

        try:
            response = requests.post(url=API_ENDPOINT, data=data)
            response.raise_for_status()

            email_data = {"subject":  "[From Tabor Remit] Card Purchase processed Sucessfully.",
                          "message": f"Hi, {customer_name}. Thank you for sending love to Ethiopia. Your card purchase \
                                order of {airtime_amount} ETB to {service_provider} \
                                customer number +251{phone_number} is completed successfully.",
                          "from_email": "our@email.com",
                          "recipient": customer_email}

            send_confirmation_mail(email_data)

        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh.response.text)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc.response.text)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt.response.text)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err.response.text)

    else:
        print("Payment invalid. Inconsistence transaction amount. Abort card purchase.")


def send_confirmation_mail(data):

   # Logic to sent fancy confirmation Email

    pass

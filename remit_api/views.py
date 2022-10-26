import json
import requests
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.shortcuts import get_object_or_404


from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView

from paypalrestsdk import notifications

from .models import (Transactions, Invoces, PackageOffers,
                     PromoCodes, Operators, PaymentMethod)
from agent_api.models import AgentProfile, ForexRate
from .serializers import (TransactionSerializer, InvoiceSerializer, PackageSerializer,
                          OperatorSerializer, PromoCodeSerializer)
from .filter import FilterTransactions


class TransactionsAdminViewset(ModelViewSet):

    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]
    filterset_class = FilterTransactions


class TransactionsListView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):

        name = self.kwargs.get('caller')

        cardPurcahase = Transactions.objects.filter(
            agent_name=name)

        if not cardPurcahase:
            raise Http404(f'No card purchase for agent named "{name}".')

        return cardPurcahase


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

        if round(Check_Amount, 2) == round(float(total), 2):
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

    def get_package_detail(self, intial_data):

        exc_rate = ForexRate.objects.get(id=1)
        USD_Amount = float(
            intial_data["selling_price_ETB"]) / float(exc_rate.forex_rate)

        package_detail = {"package_order": intial_data["package_order"],
                          "airtime_value": intial_data["airtime_value"],
                          "selling_price_ETB": intial_data["selling_price_ETB"],
                          "discount_rate": intial_data["discount_rate"],
                          "forex_rate": exc_rate.forex_rate,
                          "selling_price_USD": round(USD_Amount, 2),
                          }

        return package_detail

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=self.get_package_detail(request.data))
        if serializer.is_valid(raise_exception=True):
            pacakge = serializer.save()
            if pacakge:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def update(self, request, format=None, *args, **kwargs):

        instance = self.get_object()

        serializer = self.serializer_class(instance, data=self.get_package_detail(request.data), context={
                                           'request': request}, partial=True)

        if serializer.is_valid(raise_exception=True):
            pacakge = serializer.save()
            if pacakge:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(data=f'The {instance.airtime_value} birr package is deleted!')


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


class PromoCodeAdminViewSet(ModelViewSet):

    queryset = PromoCodes.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAdminUser]

    def get_object(self, queryset=None, *args, **kwargs):
        code = self.kwargs.get('pk')
        return get_object_or_404(PromoCodes, promo_code=code)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            pacakge = serializer.save()
            if pacakge:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def update(self, request, format=None, *args, **kwargs):

        instance = self.get_object()
        serializer = self.serializer_class(instance, request.data, context={
                                           'request': request}, partial=True)

        if serializer.is_valid(raise_exception=True):
            pacakge = serializer.save()
            if pacakge:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(data=f'Promotion code {instance.promo_code} is deleted!')


class PromoCodeRetrieveView(RetrieveAPIView):

    queryset = PromoCodes.objects.all()

    def get(self, request, **kwargs):
        code = kwargs.get('promo_code')
        try:
            promocode = PromoCodeSerializer(PromoCodes.objects.filter(
                promo_code=code, promo_expiry_date__gte=datetime.now()))
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
            process_card_purchase(event_detail)

        return HttpResponse()


def process_card_purchase(event_detail):

    order_id = event_detail["id"]
    order_amount = event_detail["purchase_units"][0]["amount"]["value"]
    customer_name = event_detail["payer"]["name"]["given_name"]
    customer_email = event_detail["payer"]["email_address"]

    try:
        Transaction_detail = Transactions.objects.get(
            transaction_id=order_id)

        if round(Transaction_detail.transaction_amount_USD, 2) == round(float(order_amount), 2):
            print("Payment Verified. Continue card purchase.")

            invoice_id = Transaction_detail.transaction_id
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

                Transaction_detail.transaction_status = "APPROVED"
                Transaction_detail.save(update_fields=['transaction_status'])

                email_data = {"subject":  "[From Tabor Remit] Card Purchase processed Sucessfully.",
                              "message": f"Hi, {customer_name}. Thank you for sending love to Ethiopia. Your card purchase \
                                    order of {airtime_amount} ETB to {service_provider} \
                                    customer number +251{phone_number} is completed successfully.\
                                        your invoice id is {invoice_id}",
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
            print(
                "Payment invalid. Inconsistence transaction amount. Abort card purchase.")

    except Transactions.DoesNotExist:
        return Response({"message": "Transaction Doesnot EXIST."}, status=status.HTTP_404_NOT_FOUND)


def send_confirmation_mail(data):

   # Logic to sent fancy confirmation Email

    print(data)

    pass

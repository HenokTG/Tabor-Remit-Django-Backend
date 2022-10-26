import json

from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse, Http404

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.generics import (
    ListCreateAPIView, UpdateAPIView, CreateAPIView, ListAPIView, RetrieveAPIView)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

from rest_framework_simplejwt.tokens import RefreshToken

from .models import (AgentProfile, PaymentsTracker,
                     NewsUpdate, Notifications, ForexRate)
from .serializers import (AgentProfileSerializer, CustomAgentSerializer, PaymentSerializer,
                          CurrencySerializer, NewsSerializer, NoticationSerializer)
from .filter import FilterPayments

from remit_api.models import Transactions


class UserRegistrationAPIView(ListCreateAPIView):

    permission_classes = [AllowAny]
    serializer_class = CustomAgentSerializer
    queryset = AgentProfile.objects.all()

    def post(self, request, format='json'):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = AgentProfileSerializer

    def get_object(self, queryset=None, **kwargs):
        user = self.kwargs.get('pk')

        return get_object_or_404(AgentProfile, agent_name=user)

    def get_queryset(self):
        return AgentProfile.objects.all()

    def update(self, request, format=None, *args, **kwargs):

        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, context={
                                           'request': request}, partial=True)

        if serializer.is_valid(raise_exception=True):
            profile = serializer.save()
            if profile:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(data=f'Agent named "{instance.agent_name}" is deleted!')


class PaymentListView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):

        name = self.kwargs.get('caller')

        payment = PaymentsTracker.objects.filter(
            agent_name=name)

        if not payment:
            raise Http404(f'No payment for agent named "{name}".')

        return payment


class PaymentViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAdminUser]
    serializer_class = PaymentSerializer
    filterset_class = FilterPayments

    queryset = PaymentsTracker.objects.all()

    def get_object(self, queryset=None, **kwargs):
        pk = self.kwargs.get('pk')

        return get_object_or_404(PaymentsTracker, id=pk)

    def get_queryset(self):
        return PaymentsTracker.objects.all()

    def check_agent(self, agent):
        try:
            agentCheck = AgentProfile.objects.get(agent_name=agent)
            return agentCheck.agent_name
        except AgentProfile.DoesNotExist:
            return f"Invalid Agent Name: {agent}"

    def get_payment_detail(self, intial_data, name, total_agent, total):

        payment_detail = {"payment_type": intial_data["paymentType"],
                          "payment_bank": intial_data["paymentBank"],
                          "transaction_number": intial_data["txnNumber"],
                          "paid_amount": round(float(intial_data["paidAmount"]), 2),
                          "total_payment": round(total, 2),
                          "total_agent_payment": round(total_agent, 2),
                          "agent_name": name,
                          }

        return payment_detail

    def create(self, request, format='json'):

        checked_agent_name = self.check_agent(request.data["AgentCode"])

        # Total Agent Payment
        try:
            all_agent_payments = self.queryset.filter(
                agent_name=request.data["AgentCode"])
            prev_agent_payment = all_agent_payments.aggregate(
                Sum('paid_amount'))['paid_amount__sum']
            if prev_agent_payment:
                total_agent_payment = float(prev_agent_payment) + \
                    float(request.data["paidAmount"])
            else:
                total_agent_payment = float(request.data["paidAmount"])
        except PaymentsTracker.DoesNotExist:
            total_agent_payment = float(request.data["paidAmount"])

        # Total Payment
        try:
            prev_payment = self.queryset.aggregate(
                Sum('paid_amount'))['paid_amount__sum']
            if prev_payment:
                total_payment = float(prev_payment) + \
                    float(request.data["paidAmount"])
            else:
                total_payment = float(request.data["paidAmount"])
        except PaymentsTracker.DoesNotExist:
            total_payment = float(request.data["paidAmount"])

        serializer = self.serializer_class(data=self.get_payment_detail(
            request.data, checked_agent_name, total_agent_payment, total_payment))

        if serializer.is_valid():
            payment = serializer.save()
            if payment:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, format='json', *args, **kwargs):

        checked_agent_name = self.check_agent(request.data["AgentCode"])

        instance = self.get_object()

        if instance.agent_name == checked_agent_name:
            # Total Agent Payment
            total_agent_payment = instance.total_agent_payment - \
                instance.paid_amount+float(request.data["paidAmount"])
            # Total Service Payment
            total_payment = instance.total_payment - \
                instance.paid_amount+float(request.data["paidAmount"])

            serializer = self.serializer_class(instance, data=self.get_payment_detail(
                request.data, checked_agent_name, total_agent_payment, total_payment), context={
                'request': request}, partial=True)

            if serializer.is_valid(raise_exception=True):
                payment = serializer.save()
                if payment:
                    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data=f'The new agent name, {checked_agent_name} does not match with old agent name {instance.agent_name}.')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        all_payments = self.queryset.filter(
            id__gte=instance.id)
        for payment in all_payments:
            payment.total_payment -= instance.paid_amount
            payment.total_agent_payment -= instance.paid_amount
            payment.save()
        instance.delete()
        return Response(data=f'Payment amount {instance.paid_amount} birr for {instance.agent_name} is deleted!')


def retrieve_4_Dashboard(request, **kwargs):

    agent = AgentProfile.objects.get(agent_name=kwargs.get('caller'))

    if agent.is_superuser and kwargs.get('task') == "retrieve":
        payment = PaymentsTracker.objects.all()
        card_purchase = Transactions.objects.all().filter(transaction_status="APPROVED")

    else:
        payment = PaymentsTracker.objects.filter(
            agent_name=kwargs.get('caller'))
        card_purchase = Transactions.objects.filter(
            agent_name=kwargs.get('caller'), transaction_status="APPROVED")

    total_payment_amount = payment.aggregate(
        Sum('paid_amount'))['paid_amount__sum']
    total_sells_amount = card_purchase.aggregate(
        Sum('sells_amount_ETB'))['sells_amount_ETB__sum']
    total_commision_amount = card_purchase.aggregate(
        Sum('payment_owed'))['payment_owed__sum']
    no_of_card_sells = card_purchase.count()

    if total_sells_amount == None:
        total_sells_amount = 0
    if total_commision_amount == None:
        total_commision_amount = 0
    if total_payment_amount == None:
        total_payment_amount = 0

    remaining_amount = float(total_commision_amount) - \
        float(total_payment_amount)

    summary = {
        "no_of_sells": no_of_card_sells,
        "total_sells": total_sells_amount,
        "total_commission": total_commision_amount,
        "reimbursed_amount": total_payment_amount,
        "remaining_amount": remaining_amount,
    }

    return HttpResponse(json.dumps(summary), status=status.HTTP_200_OK)


class PublishNewsView(CreateAPIView):

    permission_classes = [IsAdminUser]
    serializer_class = NewsSerializer
    queryset = NewsUpdate.objects.all()


class NewsHeadlineView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = NewsSerializer
    queryset = NewsUpdate.objects.all()


class NewsDetailView(RetrieveAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = NewsSerializer
    queryset = NewsUpdate.objects.all()


class NotificationsCreateView(CreateAPIView):

    permission_classes = [IsAdminUser]
    serializer_class = NoticationSerializer
    queryset = Notifications.objects.all()


class NotificationsListView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = NoticationSerializer

    def get_queryset(self):

        name = self.kwargs.get('caller')

        notice = Notifications.objects.filter(
            reciever_agent=name)

        if not notice:
            raise Http404(f'No notification for agent named "{name}".')

        return notice


class MarkReadSingleNotifications(UpdateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = NoticationSerializer
    queryset = Notifications.objects.all()

    def get_object(self, queryset=None, **kwargs):
        pk = self.kwargs.get('pk')

        return get_object_or_404(Notifications, id=pk)

    def put(self, request, format='json', *args, **kwargs):
        instance = self.get_object()
        instance.is_unread = False
        instance.save()

        return Response("One notification is marked as READ.", status=status.HTTP_202_ACCEPTED)


def MarkReadAllNotifications(request, **kwargs):

    agent_name = kwargs.get('caller')
    try:
        all_notice_for_agent = Notifications.objects.filter(
            reciever_agent=agent_name, is_unread=True)
        all_notice_for_agent.update(is_unread=False)

        return HttpResponse(f'All notifications for agent named "{agent_name}" marked as READ.', status=status.HTTP_200_OK)
    except Notifications.DoesNotExist:
        return HttpResponse(f'No notifications to mark as READ for agent named "{agent_name}".', status=status.HTTP_404_NOT_FOUND)


class CurrencyViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAdminUser]
    serializer_class = CurrencySerializer
    queryset = ForexRate.objects.all()


class BlacklistTokenUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(request.data)
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

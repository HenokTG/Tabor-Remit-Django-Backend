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
    queryset = PaymentsTracker.objects.all()

    def get_queryset(self):

        name = self.kwargs.get('caller')
        agent_id = AgentProfile.objects.get(
            agent_name=name).id

        payment = self.queryset.objects.filter(
            paid_agent=agent_id)

        return payment

    def list(self, request, *args, **kwargs):

        payments = self.get_queryset()
        if not payments:
            name = kwargs.get('caller')
            raise Http404(f'No payment for agent "{name}".')

        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class PaymentListCreateView(ListCreateAPIView):

    permission_classes = [IsAdminUser]
    serializer_class = PaymentSerializer
    queryset = PaymentsTracker.objects.all()
    filterset_class = FilterPayments

    def get_object(self, queryset=None, **kwargs):
        pk = self.kwargs.get('pk')

        return get_object_or_404(PaymentsTracker, pk=pk)

    def get_queryset(self):
        return PaymentsTracker.objects.all()

    def create(self, request, format='json'):

        card_purchase = Transactions.objects.get(
            transaction_id=request.data["cardPurchaseID"])
        paid_amount = card_purchase.payment_owed
        agent = card_purchase.invoice.agent

        # Total Agent Payment
        all_agent_payments = self.queryset.filter(
            paid_agent=agent.id)
        if all_agent_payments:
            prev_agent_payment = all_agent_payments.aggregate(
                Sum('paid_amount'))['paid_amount__sum']
            if prev_agent_payment:
                total_agent_payment = float(
                    prev_agent_payment) + float(paid_amount)
            else:
                total_agent_payment = float(paid_amount)
        else:
            total_agent_payment = float(paid_amount)

        # Total Payment
        prev_payment = self.queryset.aggregate(
            Sum('paid_amount'))['paid_amount__sum']
        if prev_payment:
            total_payment = float(prev_payment) + float(paid_amount)
        else:
            total_payment = float(paid_amount)

        payment_detail = {"payment_type": request.data["paymentType"],
                          "payment_bank": request.data["paymentBank"],
                          "transaction_number": request.data["txnNumber"],
                          "card_paid_id": request.data["cardPurchaseID"],
                          "paid_amount": round(float(paid_amount), 2),
                          "total_payment": round(total_payment, 2),
                          "total_agent_payment": round(total_agent_payment, 2),
                          "paid_agent": AgentProfile.objects.get(id=agent.id),
                          }

        serializer = self.serializer_class(data=payment_detail)

        if serializer.is_valid():
            payment = serializer.save()
            if payment:
                card_purchase.is_commission_paid = True
                card_purchase.save()
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
def retrieve_4_Dashboard(request, **kwargs):

    agent = AgentProfile.objects.get(agent_name=kwargs.get('caller'))

    if agent.is_superuser and kwargs.get('task') == "retrieve":
        payment = PaymentsTracker.objects.all()
        card_purchase = Transactions.objects.all().filter(transaction_status="APPROVED")

    else:
        payment = PaymentsTracker.objects.filter(
            paid_agent=agent.id)
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

    def post(self, request, format='json'):

        agent = AgentProfile.objects.get(
            agent_name=request.data["reciever_agent"])
        request.data["reciever_agent"] = agent

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            notice = serializer.save()
            if notice:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationsListView(ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = NoticationSerializer

    def get_queryset(self):

        agent_id = AgentProfile.objects.get(
            agent_name=self.kwargs.get('caller')).id

        notice = Notifications.objects.filter(reciever_agent=agent_id)

        return notice

    def list(self, request, *args, **kwargs):

        notifications = self.get_queryset()
        if not notifications:
            name = kwargs.get('caller')
            raise Http404(f'No notification for agent "{name}".')

        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


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

    agent = AgentProfile.objects.get(
        agent_name=kwargs.get('caller'))
    try:
        all_notice_for_agent = Notifications.objects.filter(
            reciever_agent=agent.id, is_unread=True)
        all_notice_for_agent.update(is_unread=False)

        return HttpResponse(f'All notifications for agent "{agent.agent_name}" marked as READ.', status=status.HTTP_200_OK)
    except Notifications.DoesNotExist:
        return HttpResponse(f'No notifications to mark as READ for agent "{agent.agent_name}".', status=status.HTTP_404_NOT_FOUND)


class CurrencyViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAdminUser]
    serializer_class = CurrencySerializer
    queryset = ForexRate.objects.all()

    def post(self, request, format='json'):

        agent = AgentProfile.objects.get(
            agent_name=request.data["updated_by"])
        request.data["updated_by"] = agent

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            forex_rate = serializer.save()
            if forex_rate:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlacklistTokenUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

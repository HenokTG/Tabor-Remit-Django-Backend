from django_filters import rest_framework as filters
from django_filters import CharFilter, DateFilter

from .models import Transactions


class FilterTransactions(filters.FilterSet):

    Status = CharFilter(
        field_name='transaction_status', lookup_expr='iexact')
    Airtime = CharFilter(
        field_name='airtime_amount', lookup_expr='iexact')
    Agent = CharFilter(field_name='agent_name', lookup_expr='iexact')
    Paid = CharFilter(
        field_name='is_commission_paid', lookup_expr='iexact')

    class Meta:

        fields = ['Status', 'Airtime', 'Agent', 'Paid']

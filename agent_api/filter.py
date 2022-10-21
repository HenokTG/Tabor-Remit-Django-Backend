from django_filters import rest_framework as filters
from django_filters import CharFilter, DateFilter

from .models import PaymentsTracker


class FilterPayments(filters.FilterSet):

    Payment_Type = CharFilter(field_name='payment_type', lookup_expr='iexact')
    Payment_Bank = CharFilter(field_name='payment_bank', lookup_expr='iexact')
    Agent_Name = CharFilter(field_name='agent_name', lookup_expr='iexact')

    class Meta:
        model = PaymentsTracker
        fields = ['Payment_Type', 'Payment_Bank', 'Agent_Name']

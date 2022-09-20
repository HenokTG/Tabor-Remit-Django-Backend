from rest_framework.serializers import ModelSerializer

from .models import (Transactions, Invoces, PackageOffers,
                     PromoCodes, Operators)


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transactions
        fields = '__all__'
        depth = 2


class InvoiceSerializer(ModelSerializer):
    class Meta:
        model = Invoces
        fields = '__all__'


class PackageSerializer(ModelSerializer):
    class Meta:
        model = PackageOffers
        fields = '__all__'
        
        
class OperatorSerializer(ModelSerializer):
    class Meta:
        model = Operators
        fields = '__all__'


class PromoCodeSerializer(ModelSerializer):
    class Meta:
        model = PromoCodes
        fields = '__all__'

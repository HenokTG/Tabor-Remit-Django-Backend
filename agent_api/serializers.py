from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

from .models import AgentProfile, PaymentsTracker


class CustomAgentSerializer(ModelSerializer):

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=AgentProfile.objects.all())]
    )
    agent_name = serializers.CharField(required=True, validators=[
                                     UniqueValidator(queryset=AgentProfile.objects.all())])
    phone = serializers.IntegerField(required=True,)
    password = serializers.CharField(
        min_length=8, required=True, validators=[validate_password])
    Confirm_Password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = AgentProfile
        fields = ('agent_name',
                  'email',
                  "phone",
                  "commission",
                  'password',
                  'Confirm_Password')
        extra_kwargs = {'Confirm_Password': {'write_only': True}}

    def validate(self, attrs):
        
        if attrs['password'] != attrs['Confirm_Password']:
            raise serializers.ValidationError(
                {"Confirm_Password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(
            agent_name=validated_data['agent_name'],
            email=validated_data['email'],
            Institute=validated_data['phone'])
        if password is not None:
            instance.set_password(password)
        instance.save()

        return instance


class AgentProfileSerializer(ModelSerializer):

    class Meta:
        model = AgentProfile
        exclude = ('date_joined', 'is_staff', 'is_active', 'is_superuser',
                   'password', 'last_login', 'groups', 'user_permissions')
        
class PaymentSerializer(ModelSerializer):

    class Meta:
        model = PaymentsTracker
        fields = ('payment_type', 'payment_bank',
                  'transaction_number', 'paid_amount')

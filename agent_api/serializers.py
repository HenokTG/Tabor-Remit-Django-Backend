from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

from .models import (AgentProfile, PaymentsTracker,
                     ForexRate, NewsUpdate, Notifications)


class CustomAgentSerializer(ModelSerializer):

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=AgentProfile.objects.all())]
    )
    agent_name = serializers.CharField(required=True, validators=[
        UniqueValidator(queryset=AgentProfile.objects.all())])
    phone = serializers.IntegerField(required=True,)
    commission = serializers.FloatField(default=None)
    is_active = serializers.BooleanField(default=False)
    password = serializers.CharField(
        min_length=8, required=True, validators=[validate_password])
    Confirm_Password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = AgentProfile
        fields = ('agent_name',
                  'email',
                  "phone",
                  'commission',
                  'is_active',
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

        if validated_data['is_active']:
            active = validated_data['is_active']
        else:
            active = False
        if validated_data['commission']:
            comm = validated_data['commission']
        else:
            comm = None

        instance = self.Meta.model(
            agent_name=validated_data['agent_name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            is_active=active,
            commission=comm,
        )
        if password is not None:
            instance.set_password(password)
        instance.save()

        return instance


class AgentProfileSerializer(ModelSerializer):

    class Meta:
        model = AgentProfile
        exclude = ('date_joined', 'is_staff', 'password',
                   'last_login', 'groups', 'user_permissions')


class PaymentSerializer(ModelSerializer):

    class Meta:
        model = PaymentsTracker
        fields = '__all__'
        depth = 1

    def create(self, validated_data):

        payment = self.Meta.model(**validated_data)
        payment.paid_agent = self.initial_data["paid_agent"]

        payment.save()

        return validated_data


class NewsSerializer(ModelSerializer):

    class Meta:
        model = NewsUpdate
        fields = "__all__"


class NoticationSerializer(ModelSerializer):

    class Meta:
        model = Notifications
        fields = "__all__"
        depth = 1

    def create(self, validated_data):

        notice = self.Meta.model(**validated_data)
        notice.reciever_agent = self.initial_data["reciever_agent"]

        notice.save()

        return validated_data


class CurrencySerializer(ModelSerializer):

    class Meta:
        model = ForexRate
        fields = "__all__"
        depth = 1

import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

from PIL import Image
import model_helpers


class CustomAccountManager(BaseUserManager):

    def create_superuser(self, agent_name, email, password, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must be assigned to is_staff=True.')
        if other_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must be assigned to is_superuser=True.')

        return self.create_user(agent_name, email, password, **other_fields)

    def create_user(self, agent_name, email, password, **other_fields):

        if not agent_name:
            raise ValueError(_('You must provide user name'))
        if not email:
            raise ValueError(_('You must provide an email address'))

        email = self.normalize_email(email)
        user = self.model(email=email, agent_name=agent_name,
                          **other_fields)
        user.set_password(password)
        user.save()
        return user


class AgentProfile(AbstractBaseUser, PermissionsMixin):

    agent_name = models.CharField(max_length=50, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(null=True, blank=True,
                              upload_to=model_helpers.upload_to)
    
    business_name = models.CharField(max_length=150, null=True, blank=True)
    commission = models.FloatField(max_length=10, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    phone = models.BigIntegerField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    zone = models.CharField(max_length=100, null=True, blank=True)
    woreda = models.CharField(max_length=100, null=True, blank=True)
    street = models.CharField(max_length=100, null=True, blank=True)
    
    date_joined = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomAccountManager()

    USERNAME_FIELD = 'agent_name'
    REQUIRED_FIELDS = ['email', 'commission', 'phone']

    def __str__(self):
        return f'{self.agent_name} Profile'

    def save(self,  *args, **kwargs):
        super(AgentProfile, self).save(*args, **kwargs)
        
        try:
            img = Image.open(self.image.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)
        except:
            pass

        
class PaymentsTracker(models.Model):

    payment_time = models.DateTimeField(default=timezone.now)
    payment_id = models.CharField(max_length=150,
                                  primary_key=True,
                                  default=uuid.uuid4,
                                  editable=False)
    payment_type = models.CharField(null=True, blank=True)
    payment_bank = models.CharField(null=True, blank=True)
    transaction_number = models.CharField(null=True, blank=True)
    paid_amount = models.FloatField(null=True, blank=True)
    total_sell = models.FloatField(null=True, blank=True)
    commision = models.FloatField(null=True, blank=True)
    total_payment = models.FloatField(null=True, blank=True)
    remaining_payment = models.FloatField(null=True, blank=True)
    payment_for = models.ForeignKey(settings.AUTH_USER_MODEL, default=0,
                              on_delete=models.SET_DEFAULT)

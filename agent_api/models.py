from email.policy import default
import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

from PIL import Image
import model_helpers

from remit_api.models import PackageOffers, PromoCodes


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
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    image = models.ImageField(null=True, blank=True,
                              upload_to=model_helpers.upload_to)

    phone = models.BigIntegerField(null=True, blank=True)
    commission = models.FloatField(max_length=10, null=True, blank=True)
    business_name = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
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
    REQUIRED_FIELDS = ['email', 'phone']

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


# Create or retrieve a default agent placeholder on delete
def get_default_agent():
    return AgentProfile.objects.get_or_create(agent_name="deleted", email="unknown@deleted.com", phone=0)[0].id


class PaymentsTracker(models.Model):

    payment_time = models.DateTimeField(default=timezone.now)
    card_paid_id = models.CharField(max_length=150, null=True, blank=True)
    payment_type = models.CharField(max_length=150, null=True, blank=True)
    payment_bank = models.CharField(max_length=150, null=True, blank=True)
    transaction_number = models.CharField(
        max_length=150, null=True, blank=True)
    paid_amount = models.FloatField(null=True, blank=True)
    total_payment = models.FloatField(null=True, blank=True)
    total_agent_payment = models.FloatField(null=True, blank=True)
    paid_agent = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_DEFAULT,
                                   default=get_default_agent
                                   )

    class Meta:
        ordering = ('-payment_time',)

    def __str__(self):
        return f'{self.paid_amount} birr payment for agent {self.paid_agent.agent_name}, the total is {self.total_agent_payment}'


class NewsUpdate(models.Model):

    update_time = models.DateTimeField(default=timezone.now)
    news_title = models.CharField(max_length=150, null=True, blank=True)
    news_content = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('-update_time',)

    def __str__(self):
        return f'{self.news_title}'


class Notifications(models.Model):

    notification_time = models.DateTimeField(default=timezone.now)
    task = models.CharField(max_length=144, null=True, blank=True)
    notice = models.TextField(null=True, blank=True)
    is_unread = models.BooleanField(default=True)
    reciever_agent = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.SET_DEFAULT,
                                       default=get_default_agent
                                       )

    class Meta:
        ordering = ('-notification_time',)

    def __str__(self):
        return f'Notice for {self.reciever_agent.agent_name} about {self.task}'


class ForexRate(models.Model):

    update_on = models.DateTimeField(default=timezone.now)
    from_currency = models.CharField(default="USD", max_length=10)
    to_currency = models.CharField(default="ETB", max_length=10)
    forex_rate = models.FloatField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_DEFAULT,
                                   default=get_default_agent
                                   )

    def __str__(self):
        return f'{self.id} Forex rate from {self.from_currency} to {self.to_currency} is {self.forex_rate}, updated on {self.update_on.date()}'


@receiver(post_save, sender=ForexRate)
def update_package(sender, instance, **kwargs):

    packages = PackageOffers.objects.all()

    for pack in packages:
        if pack.selling_price_ETB != None:
            pack.forex_rate = instance.forex_rate

            pack.selling_price_USD = pack.selling_price_ETB/instance.forex_rate
            pack.save()


@receiver(post_save, sender=AgentProfile)
def send_agent_created_notice(sender, instance, created, *args, **kwargs):

    task = "New agent created."
    content = f'Agent named {instance.agent_name} is created. Please check the profile and activate the agent if not activated.'

    task_agent = "Congratulation, You are registered to our service as an Agent"
    content_agent = f'Thank you for choosing to work with us. Update you profile to let us \
                                get to know you better. We look forward to profitable future with you.'

    if created and instance.is_superuser == False and instance.agent_name != "deleted":
        super_agents = AgentProfile.objects.filter(is_superuser=True)
        for admin in super_agents:
            Notifications.objects.create(reciever_agent=admin,
                                         task=task, notice=content,
                                         )
        Notifications.objects.create(reciever_agent=instance,
                                     task=task_agent, notice=content_agent,
                                     )


@receiver(post_save, sender=PaymentsTracker)
def send_payment_made_notice(sender, instance, created, *args, **kwargs):

    task = "New payment made."
    content = f'You have received reimbursement in amount of {round(instance.paid_amount,2)} birr. Thanks for partnering with us.'

    if created and instance.paid_agent.agent_name != "deleted":
        Notifications.objects.create(reciever_agent=instance.paid_agent,
                                     task=task, notice=content,

                                     )


@receiver(post_save, sender=PromoCodes)
def new_promo_code_notice(sender, instance, created, *args, **kwargs):

    title = "New promocode available"
    content = f'We glad to announce new promoter named "{instance.promoter}" with promocode "{instance.promo_code}".\
                        Our custommers will have a {round(instance.promo_discount_rate*100,2)} % until "{instance.promo_expiry_date}" \
                            if they choose to use it. Spread the good news. Thank you.'

    if created and instance.id == 0:
        NewsUpdate.objects.create(news_title=title, news_content=content,)

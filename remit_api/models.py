import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class PackageOffers(models.Model):

    package_order = models.IntegerField(null=True, blank=True)
    airtime_value = models.FloatField(null=True, blank=True)
    selling_price_ETB = models.FloatField(null=True, blank=True)
    forex_rate = models.FloatField(null=True, blank=True)
    selling_price_USD = models.FloatField(null=True, blank=True)
    discount_rate = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.airtime_value} ETB Package Offer'

    class Meta:
        ordering = ('package_order',)
        verbose_name_plural = "Package Offers"
        verbose_name = "Package Offer Detail"


class PromoCodes(models.Model):

    promoter = models.CharField(max_length=150, null=True, blank=True)
    promo_code = models.CharField(
        max_length=50, unique=True, null=True, blank=True)
    promo_discount_rate = models.FloatField(null=True, blank=True)
    promo_expiry_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Promoter: {self.promoter} - Promo Code: {self.promo_code}'

    class Meta:
        ordering = ('promoter',)
        verbose_name_plural = "Promotion Discount Listings"
        verbose_name = "Promotion Discount Detail"


class Operators(models.Model):

    operator_name = models.CharField(max_length=50, null=True, blank=True)
    operator_order = models.IntegerField(null=True, blank=True)
    operator_discount_rate = models.FloatField(null=True, blank=True)
    operator_image_link = models.TextField(null=True, blank=True)
    operator_active = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f'Operator: {self.operator_name} - Operating: {self.operator_active}'

    class Meta:
        verbose_name_plural = "Mobile Network Operators"
        verbose_name = "Network Operator Info"


class PaymentMethod(models.Model):

    provider_name = models.CharField(max_length=50, null=True, blank=True)
    provider_order = models.IntegerField(null=True, blank=True)
    provider_image_link = models.TextField(null=True, blank=True)
    provider_active = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f'Payment Method: {self.provider_name}'

    class Meta:
        verbose_name_plural = "Payment Providers list"
        verbose_name = "Payment Provider"


class Invoces(models.Model):

    invoices_commit = models.DateTimeField(default=timezone.now)
    invoive_id = models.CharField(max_length=150,
                                  primary_key=True,
                                  default=uuid.uuid4,
                                  editable=False)
    receiver_phone = models.IntegerField(null=True, blank=True)
    package_offers = models.ForeignKey(
        PackageOffers,  default=None, on_delete=models.SET_DEFAULT, null=True, blank=True)
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, default=None,
                              on_delete=models.SET_DEFAULT, null=True, blank=True)
    promo_code = models.ForeignKey(
        PromoCodes,  default=None, on_delete=models.SET_DEFAULT, null=True, blank=True)
    operator = models.ForeignKey(
        Operators,  default=None, on_delete=models.SET_DEFAULT, null=True, blank=True)
    payment_method = models.ForeignKey(
        PaymentMethod, default=None, on_delete=models.SET_DEFAULT, null=True, blank=True)

    def __str__(self):

        if self.package_offers.airtime_value:
            airtime_value = self.package_offers.airtime_value
        else:
            airtime_value = "Unknown: Deleted package"

        return f'Invoice number: {self.invoive_id} - Reciever: +251{self.receiver_phone} - Amount: {airtime_value}'

    class Meta:
        verbose_name_plural = "Invoce Records"
        verbose_name = "Invoices Detail"


class Transactions(models.Model):

    transaction_id = models.CharField(max_length=150,
                                      primary_key=True,
                                      default=uuid.uuid4,
                                      editable=False)

    invoice = models.OneToOneField(
        Invoces,
        on_delete=models.CASCADE,
    )

    committed_on = models.DateTimeField(null=True, blank=True)
    transaction_status = models.CharField(max_length=50, default="COMMITTED")
    transaction_amount_USD = models.FloatField(null=True, blank=True)
    airtime_amount = models.FloatField(null=True, blank=True)
    sells_amount_ETB = models.FloatField(null=True, blank=True)
    agent_name = models.CharField(max_length=50, null=True, blank=True)
    commision = models.FloatField(null=True, blank=True)
    payment_owed = models.FloatField(null=True, blank=True)
    is_commission_paid = models.BooleanField(default=False)

    def __str__(self):
        return f'Phone: {self.invoice.receiver_phone} - Card: {self.airtime_amount} - Status: {self.transaction_status} - Amount:  {self.transaction_amount_USD}'

    class Meta:
        verbose_name_plural = "Transactions Records"
        verbose_name = "Transactions Detail"


@receiver(post_save, sender=Invoces)
def manage_transaction(sender, instance, created, *args, **kwargs):

    remit_value = instance.package_offers.airtime_value
    selling_price_ETB = instance.package_offers.selling_price_ETB
    selling_price_USD = instance.package_offers.selling_price_USD
    service_discount = instance.package_offers.discount_rate
    operator_discount = instance.operator.operator_discount_rate
    agent_pay = selling_price_ETB * instance.agent.commission

    if instance.promo_code == None:
        promo_disc = 0
    else:
        promo_disc = instance.promo_code.promo_discount_rate

    Sells_amount_ETB = selling_price_ETB * (1 - service_discount) * \
        (1-operator_discount) * (1-promo_disc)
    Paid_Amount_USD = selling_price_USD * (1 - service_discount) * \
        (1-operator_discount) * (1-promo_disc)

    if created:
        Transactions.objects.create(transaction_id=instance.invoive_id,
                                    committed_on=instance.invoices_commit,
                                    airtime_amount=remit_value,
                                    sells_amount_ETB=round(
                                        Sells_amount_ETB, 2),
                                    transaction_amount_USD=round(
                                        Paid_Amount_USD, 2),
                                    agent_name=instance.agent.agent_name,
                                    commision=instance.agent.commission,
                                    payment_owed=agent_pay,
                                    invoice=instance,)
    else:
        Transaction = Transactions.objects.get(
            transaction_id=instance.invoive_id)
        Transaction.update(committed_on=instance.invoices_commit,
                           airtime_amount=remit_value,
                           sells_amount_ETB=round(
                               Sells_amount_ETB, 2),
                           transaction_amount_USD=round(
                               Paid_Amount_USD, 2),
                           agent_name=instance.agent.agent_name,
                           commision=instance.agent.commission,
                           payment_owed=agent_pay,
                           invoice=instance,)
        Transaction.save()

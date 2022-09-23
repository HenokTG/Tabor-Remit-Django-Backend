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
    selling_price_USD = models.FloatField(null=True, blank=True)
    discount_rate = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'{self.airtime_value} ETB Package Offer'

    class Meta:
        verbose_name_plural = "Package Offers"
        verbose_name = "Package Offer Detail"


class PromoCodes(models.Model):

    promoter = models.CharField(max_length=150, null=True, blank=True)
    promo_code = models.CharField(max_length=50, null=True, blank=True)
    promo_discount_rate = models.FloatField(null=True, blank=True)
    promo_expiry_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Promoter: {self.promoter} - Promo Code: {self.promo_code}'

    class Meta:
        verbose_name_plural = "Promotion Discount Listings"
        verbose_name = "Promotion Discount Detail"


class Operators(models.Model):

    operator_name = models.CharField(max_length=50, null=True, blank=True)
    operator_order = models.IntegerField(null=True, blank=True)
    operator_discount_rate = models.FloatField(null=True, blank=True)
    operator_image_link = models.CharField(
        max_length=1000, null=True, blank=True)
    operator_active = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f'Operator: {self.operator_name} - Operating: {self.operator_active}'

    class Meta:
        verbose_name_plural = "Mobile Network Operators"
        verbose_name = "Network Operator Info"


class PaymentMethod(models.Model):

    provider_name = models.CharField(max_length=50, null=True, blank=True)
    provider_order = models.IntegerField(null=True, blank=True)
    provider_image_link = models.CharField(
        max_length=1000, null=True, blank=True)
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
    package_offers = models.ForeignKey(PackageOffers, on_delete=models.CASCADE)
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, default=0,
                              on_delete=models.SET_DEFAULT)
    promo_code = models.ForeignKey(PromoCodes, default=0,
                                   on_delete=models.SET_DEFAULT, null=True, blank=True)
    operator = models.ForeignKey(Operators, default=0,
                                 on_delete=models.SET_DEFAULT)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)

    def __str__(self):
        return f'Invoice number: {self.invoive_id} - Reciever: +251{self.receiver_phone} - Amount: {self.package_offers.airtime_value}'

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

    transaction_status = models.CharField(max_length=50, null=True, blank=True)
    transaction_amount = models.FloatField(null=True, blank=True)
    airtime_amount = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f'Phone: {self.invoice.receiver_phone} - Status: {self.transaction_status} - Amount:  {self.transaction_amount}'

    class Meta:
        verbose_name_plural = "Transactions Records"
        verbose_name = "Transactions Detail"


@receiver(post_save, sender=Invoces)
def create_transaction(sender, instance, created, *args, **kwargs):

    remit_value = instance.package_offers.airtime_value
    selling_price = instance.package_offers.selling_price_USD
    service_discount = instance.package_offers.discount_rate
    operator_discount = instance.operator.operator_discount_rate

    if instance.promo_code == None:
        promo_disc = 0
    else:
        promo_disc = instance.promo_code.promo_discount_rate

    Paid_Amount = selling_price * (1 - service_discount) * \
        (1-operator_discount) * (1-promo_disc)
    if created:
        Transactions.objects.create(transaction_id=instance.invoive_id,
                                    airtime_amount=remit_value,
                                    invoice=instance,
                                    transaction_status="commited",
                                    transaction_amount=Paid_Amount)


@receiver(post_save, sender=Invoces)
def save_transaction(sender, instance, **kwargs):
    instance.transactions.save()

from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'admin/packages', PackagesViewSet, basename='Packages_Admin')
router.register(r'admin/promo-codes', PromoCodeAdminViewSet,
                basename='Promocodes_Admin')
router.register(r'admin/operators', OperatorAdminViewSet,
                basename='Operators_Admin')
router.register(r'admin/transactions', TransactionsAdminViewset,
                basename='Transactions_Admin')
router.register(r'admin/invoices', InvoicesAdminViewset,
                basename='Invoices_Admin')
urlpatterns = router.urls

urlpatterns += [
    path('transactions/', TransactionsListView.as_view(),
         name='transactions'),
    path('invoices/<str:order_id>', InvoicesCreateView.as_view(),
         name='Invoices'),
    path('packages/', PackageLIstView.as_view(),
         name='Packages'),
    path('operators/', OperatorLIstView.as_view(),
         name='Operators'),
    path('promo-codes/<str:promo_code>', PromoCodeRetrieveView.as_view(),
         name='Promo_Codes'),
    path('webhooks/paypal/', RemitProcessWebhookView.as_view())
]

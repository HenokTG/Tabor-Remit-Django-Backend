from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, UserRegistrationAPIView, PaymentViewSet


router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'payments', PaymentViewSet, basename='payment')
urlpatterns = router.urls

urlpatterns += [
    path('register/', UserRegistrationAPIView.as_view(), name='user_registery'),
]

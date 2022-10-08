from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (PaymentViewSet, ProfileViewSet,
                    UserRegistrationAPIView, BlacklistTokenUpdateView)


router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'profiles', ProfileViewSet, basename='profile')
urlpatterns = router.urls

urlpatterns += [
    path('register/', UserRegistrationAPIView.as_view(), name='user_registery'),
    path('logout/blacklist/', BlacklistTokenUpdateView.as_view(),
         name='blacklist')
]

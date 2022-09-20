from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, UserRegistrationAPIView


router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
urlpatterns = router.urls

urlpatterns += [
    path('register/', UserRegistrationAPIView.as_view(), name='user_registery'),
]

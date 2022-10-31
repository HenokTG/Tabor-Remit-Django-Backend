from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (PaymentListCreateView, ProfileViewSet, CurrencyViewSet,
                    PaymentListView, NotificationsCreateView,
                    NotificationsListView,
                    MarkReadSingleNotifications, PublishNewsView,
                    NewsHeadlineView,  NewsDetailView,
                    MarkReadAllNotifications, retrieve_4_Dashboard,
                    UserRegistrationAPIView, BlacklistTokenUpdateView)


router = DefaultRouter()
router.register(r'admin/currency', CurrencyViewSet, basename='profile')
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = router.urls

urlpatterns += [
    path('register/', UserRegistrationAPIView.as_view(), name='user_registery'),
    path('dashboard/summary/<str:caller>/<str:task>',
         retrieve_4_Dashboard, name='retrieve_summary'),
    path('admin/payments/', PaymentListCreateView.as_view(), name='user_registery'),
    path('list-payments/<str:caller>',
         PaymentListView.as_view(), name='list_payment'),
    path('admin/create-news/', PublishNewsView.as_view(), name='create_news'),
    path('list-news/', NewsHeadlineView.as_view(), name='list_headlines'),
    path('news-detail/<str:pk>', NewsDetailView.as_view(), name='news_detail'),
    path('admin/create-notice/',
         NotificationsCreateView.as_view(), name='create_notice'),
    path('notifications/<str:caller>/',
         NotificationsListView.as_view(), name='list_notice'),
    path('notifications/update/<str:pk>/',
         MarkReadSingleNotifications.as_view(), name='mark_read_notice'),
    path('notifications/update-all/<str:caller>/',
         MarkReadAllNotifications, name='mark_all_read_notice'),
    path('logout/blacklist/', BlacklistTokenUpdateView.as_view(),
         name='blacklist')
]

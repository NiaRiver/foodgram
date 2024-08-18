from django.urls import path, include
from .views import UserListView, UserAvatarUpdateView, SubscriptionsListView, SubscribeCreateDestroyView

SUBSCRIBE = {
    'post': 'create',
    'delete': 'destroy'
}

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/', SubscriptionsListView.as_view(), name='subs'),
    path('users/me/avatar/', UserAvatarUpdateView.as_view(), name='user_avatar_update'),
    path('users/<int:pk>/subscribe/', SubscribeCreateDestroyView.as_view(SUBSCRIBE), name='subscribe'),
    path('', include('djoser.urls')),
]
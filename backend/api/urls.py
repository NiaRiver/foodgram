from rest_framework.generics import RetrieveAPIView
from rest_framework.routers import DefaultRouter
from django.contrib.auth import get_user_model
from django.urls import path, include
from .views import ReadOnly
from .views import (
    UserAvatarUpdateView,
    SubscriptionsListView,
    RecipeViewSet,
    # RecipeListView,
    # RecipeDetailView,
    SubscribeCreateDestroyView,
    RecipeLinkView,
    TagViewSet,
    IngredientViewSet,
    FavoriteView,
    ShoppingCartView,
    DownloadShoppingListView
)
from .serializers import UserSerializer

app_name = 'api'
User = get_user_model()

SUBSCRIBE = {
    'post': 'create',
    'delete': 'destroy'
}

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingListView.as_view(),
        name='download_shopping_list'
    ),
    path(
        'recipes/<int:id>/get-link/',
        RecipeLinkView.as_view(),
        name='get-recipe-link'
    ),
    path(
        'recipes/<int:id>/shopping_cart/',
        ShoppingCartView.as_view(SUBSCRIBE),
        name='shopping_cart'
    ),
    path('', include(router.urls)),
    path('users/<int:pk>/', RetrieveAPIView.as_view(
        queryset=User.objects.all(),
        serializer_class=UserSerializer,
        permission_classes=[ReadOnly]
    ), name='user_detail'),
    path(
        'users/subscriptions/',
        SubscriptionsListView.as_view(),
        name='subscriptions'
    ),
    path(
        'users/<int:pk>/subscribe/',
        SubscribeCreateDestroyView.as_view(SUBSCRIBE),
        name='subscribe'
    ),
    path('', include('djoser.urls')),
    path(
        'users/me/avatar/',
        UserAvatarUpdateView.as_view(),
        name='user_avatar_update'
    ),
    path(
        'recipes/<int:id>/favorite/',
        FavoriteView.as_view(SUBSCRIBE),
        name='favorite'
    ),
]

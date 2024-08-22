from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    get_object_or_404,
    ValidationError
)
from rest_framework.views import APIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, AvatarSerializer, SubscriptionSerializer, SubscribeSerializer, RecipeListOrRetrieveSerializer, RecipePostOrPatchSerializer
from core.models import Subscription
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django import urls
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from .filters import RecipeFilter, Recipe
from core.models import Recipe, ShortenedRecipeURL
from .serializers import RecipeLinkSerializer

User = get_user_model()


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserAvatarUpdateView(RetrieveUpdateDestroyAPIView):
    serializer_class = AvatarSerializer

    def get_object(self):
        # Get the User object for the currently authenticated user
        return get_object_or_404(User, pk=self.request.user.id)

    def patch(self, request, *args, **kwargs):
        # Allow partial updates with the PATCH method
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'Avatar updated'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionsListView(ListAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        # Get the current user (if the user is not authenticated, you may want to handle this case)
        user = self.request.user

        # If the user is not authenticated, return an empty queryset instead of raising an error

        # Filter the subscriptions where the current user is the `subscribed_to` user
        subscriptions = Subscription.objects.filter(user=user)

        # Get the users who have subscribed to the current user
        subscribed_users = User.objects.filter(id__in=subscriptions.values('subscribed_to'))

        # Return the queryset or an empty queryset if no subscriptions exist
        return subscribed_users if subscriptions.exists() else User.objects.none()


class SubscribeCreateDestroyView(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = SubscribeSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')
        subscribed_to = get_object_or_404(User, pk=pk)
        return get_object_or_404(Subscription, user=self.request.user, subscribed_to=subscribed_to)

    def perform_create(self, serializer):
        pk = self.kwargs.get('pk')
        subscribed_to = get_object_or_404(User, pk=pk)

        # Check if the subscription already exists
        if self.request.user == subscribed_to:
            raise ValidationError("You cannot subscribe to yourself.")

        if Subscription.objects.filter(user=self.request.user, subscribed_to=subscribed_to).exists():
            raise ValidationError("You are already subscribed to this user.")

        serializer.save(user=self.request.user, subscribed_to=subscribed_to)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})  # Empty data since `subscribed_to` is set internally
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

        # Get the `subscribed_to` user instance
            subscribed_to_user = serializer.instance.subscribed_to

        # Serialize the `subscribed_to` user using the `UserDetailSerializer`
            user_detail_serializer = SubscriptionSerializer(subscribed_to_user, context={'request': request})
            data = user_detail_serializer.data

            return Response(data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            return Response({"errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    # serializer_class = RecipeListOrRetrieveSerializer

    # В зависимости от действия (list или retrieve) используем разные сериализаторы
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeListOrRetrieveSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RecipePostOrPatchSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = [
        'author', 'tags',
        # 'is_favorited', 'is_in_shopping_cart'
    ]


class RecipeLinkView(APIView):
    def get(self, request, id):
        try:
            recipe = Recipe.objects.get(pk=id)
            if not hasattr(recipe, 'shortened_url'):
                ShortenedRecipeURL.objects.create(recipe=recipe)
            serializer = RecipeLinkSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)


def redirect_to_original(request, short_code):
    url = get_object_or_404(ShortenedRecipeURL, short_code=short_code)
    return redirect(urls.reverse('api:recipe-detail', kwargs={'pk': url.recipe.id}))    

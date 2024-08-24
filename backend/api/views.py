from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    get_object_or_404,
    ValidationError,
)
from rest_framework.views import APIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer,
    AvatarSerializer,
    SubscriptionSerializer,
    SubscribeSerializer,
    RecipeListOrRetrieveSerializer,
    RecipePostOrPatchSerializer,
    TagSerializer,
    GetOrRetrieveIngredientSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    SubList
)
from core.models import Subscription, FavoriteRecipe
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django import urls
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from core.models import Recipe, ShortenedRecipeURL, Ingredient, Tag, ShoppingCart
from .filters import IngredientFilter, RecipeFilterSet
from .pagination import LimitPagination, SubLimitPagination
from .permissions import ReadOnly, IsAuthorOrReadOnly
from .serializers import RecipeLinkSerializer

User = get_user_model()


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [ReadOnly]


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
            return Response({"status": "Avatar updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            user: User = get_object_or_404(User, pk=self.request.user.id)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionsListView(ListAPIView):
    serializer_class = SubList
    pagination_class = SubLimitPagination

    def get_queryset(self): 
        user = self.request.user
        subscriptions = Subscription.objects.filter(user=user)
        subscribed_users = User.objects.filter(
            id__in=subscriptions.values("subscribed_to")
        )
        return subscriptions if subscriptions.exists() else Subscription.objects.none()


class SubscribeCreateDestroyView(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = SubscriptionSerializer

    def get_object(self):
        pk = self.kwargs.get("pk")
        subscribed_to = get_object_or_404(User, pk=pk)
        return get_object_or_404(
            Subscription, user=self.request.user, subscribed_to=subscribed_to
        )

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        subscribed_to = get_object_or_404(User, pk=pk)

        # Initialize serializer with the primary key of subscribed_to
        serializer = self.get_serializer(data={"subscribed_to": subscribed_to.id, "user": request.user.id})
        serializer.is_valid(raise_exception=True)

        # Try saving and handling potential errors
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            return Response({"errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["author", "tags"]
    filterset_class = RecipeFilterSet
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeListOrRetrieveSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return RecipePostOrPatchSerializer
        return super().get_serializer_class()


class RecipeLinkView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            recipe = Recipe.objects.get(pk=id)
            if not hasattr(recipe, "shortened_url"):
                ShortenedRecipeURL.objects.create(recipe=recipe)
            serializer = RecipeLinkSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND
            )


def redirect_to_original(request, short_code):
    url = get_object_or_404(ShortenedRecipeURL, short_code=short_code)
    return redirect(urls.reverse("api:recipe-detail", kwargs={"pk": url.recipe.id}))


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = GetOrRetrieveIngredientSerializer
    filterset_class = IngredientFilter
    permission_classes = [AllowAny]
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    serializer_class = TagSerializer
    pagination_class = None


class FavoriteView(ModelViewSet):
    queryset = FavoriteRecipe.objects.all()
    serializer_class = FavoriteSerializer
    http_method_names = ["post", "delete"]

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("id")  # Get recipe_id from URL
        recipe = get_object_or_404(Recipe, id=recipe_id)  # Retrieve the Recipe instance

        data = {"user": request.user.id, "recipe": recipe.id}

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("id")  # Get recipe_id from URL
        recipe = get_object_or_404(Recipe, id=recipe_id)  # Retrieve the Recipe instance

        try:
            favorite_recipe = FavoriteRecipe.objects.get(
                recipe=recipe, user=self.request.user
            )
            favorite_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FavoriteRecipe.DoesNotExist:
            return Response(
                {"detail": "This recipe is not in your favorites."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ShoppingCartView(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    http_method_names = ["post", "delete"]

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("id")
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = {"user": request.user.id, "recipe": recipe.id}

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(recipe=recipe, user=request.user)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("id")
        recipe = get_object_or_404(Recipe, id=recipe_id)

        shopping_cart_item = ShoppingCart.objects.filter(
            recipe=recipe, user=request.user
        ).first()
        if request.user.is_anonymous:
            return Response(
                {"detail": "You're unauthorized for this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if shopping_cart_item:
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"detail": "This recipe is not in your shopping cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )

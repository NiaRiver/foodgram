from io import BytesIO

from core.models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                         ShoppingCart, ShortenedRecipeURL, Subscription, Tag)
from django import urls
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from PyPDF2 import PdfMerger
from rest_framework import filters, generics, status
from rest_framework.generics import (ListAPIView, RetrieveUpdateDestroyAPIView,
                                     get_object_or_404)
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from .filters import IngredientFilter, RecipeFilterSet
from .pagination import LimitPagination, SubLimitPagination, paginate_list
from .permissions import IsAuthorOrReadOnly, ReadOnly
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          GetOrRetrieveIngredientSerializer,
                          RecipeLinkSerializer, RecipeListOrRetrieveSerializer,
                          RecipePostOrPatchSerializer, ShoppingCartSerializer,
                          SubList, SubscriptionSerializer, TagSerializer,
                          UserSerializer)
from .services import pdf_over_template

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
            return Response(
                {"status": "Avatar updated"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            user = get_object_or_404(User, pk=self.request.user.id)
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
        return (
            subscriptions if subscriptions.exists()
            else Subscription.objects.none()
        )


class SubscribeCreateDestroyView(
    CreateModelMixin, DestroyModelMixin, GenericViewSet
):
    serializer_class = SubscriptionSerializer

    def get_object(self):
        pk = self.kwargs.get("pk")
        subscribed_to = get_object_or_404(User, pk=pk)
        return get_object_or_404(
            Subscription, user=self.request.user, subscribed_to=subscribed_to
        )

    @staticmethod
    def perform_create(serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        subscribed_to = get_object_or_404(User, pk=pk)

        # Initialize serializer with the primary key of subscribed_to
        serializer = self.get_serializer(
            data={"subscribed_to": subscribed_to.id, "user": request.user.id}
        )
        serializer.is_valid(raise_exception=True)

        # Try saving and handling potential errors
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except ValidationError as e:
            return Response(
                {"errors": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @staticmethod
    def destroy(request, *args, **kwargs):
        user = request.user
        subscribed_to_id = kwargs.get("pk")
        try:
            author = User.objects.get(pk=subscribed_to_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Author not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        subscription = Subscription.objects.filter(
            user=user, subscribed_to=author).first()
        if not subscription:
            return Response(
                {'error': 'Subscription does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilterSet
    filterset_fields = ["author", "tags",
                        "is_favorited", "is_in_shopping_cart"]
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return RecipeListOrRetrieveSerializer
        if self.action in {"create", "update", "partial_update"}:
            return RecipePostOrPatchSerializer
        return super().get_serializer_class()


class RecipeLinkView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def get(request, id):
        try:
            recipe = Recipe.objects.get(pk=id)
            if not hasattr(recipe, "shortened_url"):
                ShortenedRecipeURL.objects.create(recipe=recipe)
            serializer = RecipeLinkSerializer(
                recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Recipe not found."},
                status=status.HTTP_404_NOT_FOUND
            )


def redirect_to_original(request, short_code):
    url = get_object_or_404(ShortenedRecipeURL, short_code=short_code)
    return redirect(
        urls.reverse(
            "api:recipe-detail", kwargs={"pk": url.recipe.id}
        )
    )


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
        # Retrieve the Recipe instance
        recipe = get_object_or_404(Recipe, id=recipe_id)

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
        # Retrieve the Recipe instance
        recipe = get_object_or_404(Recipe, id=recipe_id)

        try:
            favorite_recipe = FavoriteRecipe.objects.get(
                recipe=recipe, user=self.request.user)
            favorite_recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FavoriteRecipe.DoesNotExist:
            return Response(
                {"detail": "This recipe is not in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ShoppingCartView(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    http_method_names = ["post", "delete"]

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get("id")
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = {"user": request.user.id, "recipe": recipe.id}

        if ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                {'error': 'Recipe already in shopping cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            recipe=recipe, user=request.user).first()
        if request.user.is_anonymous:
            return Response(
                {"detail": "You're unauthorized for this action."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if shopping_cart_item:
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "This recipe is not in your shopping cart."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DownloadShoppingListView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        template = 'api/shopping_list_pdf_template.html'
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart_by__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        page_size = 25
        paginated_ingredients = paginate_list(ingredients, page_size)

        pdf_merger = PdfMerger()

        for chunk in paginated_ingredients:
            context = {
                'shopping_list': [{
                    'product': ingredient['ingredient__name'],
                    'amount': ingredient['total_amount'],
                    'unit': ingredient['ingredient__measurement_unit'],
                }
                    for ingredient in chunk
                ]}
            pdf_data = pdf_over_template(request, template, context)

            pdf_file = BytesIO(pdf_data['pdf'])
            pdf_merger.append(pdf_file)

        pdf_output = BytesIO()
        pdf_merger.write(pdf_output)
        pdf_merger.close()
        pdf_output.seek(0)
        time = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"shopping_list_{time}.pdf"
        response = HttpResponse(pdf_output, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

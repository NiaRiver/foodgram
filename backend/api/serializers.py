from base64 import b64decode

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from rest_framework.generics import ValidationError
from core.models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                         ShoppingCart, ShortenedRecipeURL, Subscription, Tag)

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            "id", "email", "username", "password", "first_name", "last_name"
        )


class UserSerializer(serializers.ModelSerializer):
    """Для получения списка пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        ]

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return user.subscriptions.filter(subscribed_to=obj).exists()


class SubList(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source="subscribed_to.username")
    first_name = serializers.ReadOnlyField(source="subscribed_to.first_name")
    last_name = serializers.ReadOnlyField(source="subscribed_to.last_name")
    avatar = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source="subscribed_to.email")
    id = serializers.ReadOnlyField(source="subscribed_to.id")

    class Meta:
        model = Subscription
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        ]

    def get_avatar(self, obj):
        if obj.subscribed_to.avatar:
            return obj.subscribed_to.avatar.url
        return None

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return user.subscriptions.filter(
            subscribed_to=obj.subscribed_to
        ).exists()

    def get_recipes(self, obj):
        recipes = obj.subscribed_to.recipes.all()
        limit = self.context["request"].query_params.get("recipes_limit", None)
        if limit:
            recipes = recipes[: int(limit)]
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url,
                "cooking_time": recipe.cooking_time,
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        return obj.subscribed_to.recipes.all().count()


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source="subscribed_to.username")
    first_name = serializers.ReadOnlyField(source="subscribed_to.first_name")
    last_name = serializers.ReadOnlyField(source="subscribed_to.last_name")
    avatar = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source="subscribed_to.email")
    subscribed_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = Subscription
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "subscribed_to",
            "avatar",
            "user"
        ]

    def validate(self, data):
        if data["user"] == data["subscribed_to"]:
            raise ValidationError(
                {"subscription": "You can't subscribe on you're self."}
            )
        return super().validate(data)

    def get_avatar(self, obj):
        if obj.subscribed_to.avatar:
            return obj.subscribed_to.avatar.url
        return None

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return user.subscriptions.filter(
            subscribed_to=obj.subscribed_to
        ).exists()

    def get_recipes(self, obj):
        limit = self.context["request"].query_params.get("recipes_limit", None)
        recipes = obj.subscribed_to.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "image": recipe.image.url,
                "cooking_time": recipe.cooking_time,
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        return obj.subscribed_to.recipes.all().count()

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr["id"] = instance.subscribed_to.id
        return repr


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["user", "subscribed_to", "created_at"]
        read_only_fields = ["user", "subscribed_to", "created_at"]


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class RecipeListOrRetrieveSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        ]

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user and user.is_authenticated:
            return obj.is_favorited_by(user)
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user and user.is_authenticated:
            return obj.is_in_shopping_cart_by(user)
        return False


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1, max_value=32_000)

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipePostOrPatchSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(min_value=1, max_value=32_000)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        ]

    def get_is_favorited(self, obj):
        return self.context["request"].user.favorite_recipes.filter(
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return self.context["request"].user.shopping_cart_recipes.filter(
            recipe=obj
        ).exists()

    def validate(self, data):
        if not data.get("tags"):
            raise ValidationError(
                {"tags": "Recipe should have at least one tag. d:"}
            )

        tags = set()
        for item in data["tags"]:
            if item in tags:
                raise ValidationError(
                    {"tags": "unique constraint failed."}
                )
            tags.add(item)

        if not data.get("ingredients"):
            raise ValidationError(
                {
                    "ingredients":
                        "Recipe should have at least one ingredient. d:"
                }
            )

        ingredient = set()
        for item in data["ingredients"]:
            if item["id"] in ingredient:
                raise ValidationError(
                    {"ingredients": "unique constraint failed."}
                )
            ingredient.add(item["id"])
        return data

    def add_ingredients(self, recipe, ingredients):
        recipe_ingredients = []

        for ingredient in ingredients:
            # Получение объекта ингредиента
            ingredient_id = ingredient.pop("id")
            recipe_ingredient = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_id,
                **ingredient
            )
            recipe_ingredients.append(recipe_ingredient)
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        # Извлечение данных ингредиентов
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)

        # Создание связей с ингредиентами
        self.add_ingredients(recipe, ingredients_data)
        recipe.refresh_from_db()
        return recipe

    def update(self, instance, validated_data):
        if validated_data.get("ingredients"):
            ingredients_data = validated_data.pop("ingredients")
            instance.ingredients.all().delete()
            self.add_ingredients(instance, ingredients_data)
        super().update(instance, validated_data)

        return instance

    def to_representation(self, instance):
        return RecipeListOrRetrieveSerializer(
            instance, context=self.context
        ).data


class RecipeLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ["short_link"]

    def get_short_link(self, obj: ShortenedRecipeURL):
        request = self.context.get("request")
        short_code = obj.shortened_url.short_code
        return request.build_absolute_uri(f"/s/{short_code}/")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["short-link"] = representation.pop("short_link")
        return representation


class GetOrRetrieveIngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.CharField()

    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ["user", "recipe"]

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "name": instance.recipe.name,
            "image": instance.recipe.image.url,
            "cooking_time": instance.recipe.cooking_time,
        }


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="recipe.id")
    image = serializers.ReadOnlyField(source="recipe.image.url")
    name = serializers.ReadOnlyField(source="recipe.name")
    cooking_time = serializers.ReadOnlyField(source="recipe.cooking_time")

    class Meta:
        model = ShoppingCart
        fields = ["id", "image", "name", "cooking_time"]

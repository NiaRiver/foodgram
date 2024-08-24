from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import serializers
from base64 import b64decode
from io import BytesIO
from PIL import Image
from rest_framework.generics import ValidationError
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework.generics import get_object_or_404
from core.models import (
    Subscription,
    RecipeIngredient,
    Recipe,
    Tag,
    Ingredient,
    ShortenedRecipeURL,
    FavoriteRecipe,
    ShoppingCart,
)

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ("id", "email", "username", "password", "first_name", "last_name")


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
        return Subscription.objects.filter(user=user, subscribed_to=obj).exists()


class SubList(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source="subscribed_to.username")
    first_name = serializers.ReadOnlyField(source="subscribed_to.first_name")
    last_name = serializers.ReadOnlyField(source="subscribed_to.last_name")
    avatar = serializers.SerializerMethodField()  # Changed to SerializerMethodField
    email = serializers.ReadOnlyField(source="subscribed_to.email")
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

    def get_avatar(self, obj):  # New method to handle avatar safely
        if obj.subscribed_to.avatar:
            return obj.subscribed_to.avatar.url
        return None

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, subscribed_to=obj.subscribed_to).exists()

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.subscribed_to)
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
        return Recipe.objects.filter(author=obj.subscribed_to).count()

class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source="subscribed_to.username")
    first_name = serializers.ReadOnlyField(source="subscribed_to.first_name")
    last_name = serializers.ReadOnlyField(source="subscribed_to.last_name")
    avatar = serializers.SerializerMethodField()  # Changed to SerializerMethodField
    email = serializers.ReadOnlyField(source="subscribed_to.email")
    subscribed_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)

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
        ]

    def validate(self, data):
        if data['user'] == data['subscribed_to']:
            raise ValidationError({"subscription": "You can't subscribe on you're self."})
        return super().validate(data)

    def get_avatar(self, obj):  # New method to handle avatar safely
        if obj.subscribed_to.avatar:
            return obj.subscribed_to.avatar.url
        return None

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, subscribed_to=obj.subscribed_to).exists()

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.subscribed_to)
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
        return Recipe.objects.filter(author=obj.subscribed_to).count()

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr["id"] = instance.subscribed_to.id
        return repr

    def to_internal_value(self, data):
        repr = super().to_internal_value(data)
        repr['subscribed_to'] = data['subscribed_to']
        repr['user'] = data['user']
        return repr

    def create(self, validated_data):
        subscribed_to = User.objects.get(pk=validated_data['subscribed_to'])
        user = User.objects.get(pk=validated_data['user'])

        # Check for existing subscription
        if Subscription.objects.filter(user=user, subscribed_to=subscribed_to).exists():
            raise ValidationError("You are already subscribed to this user.")

        return Subscription.objects.create(user=user, subscribed_to=subscribed_to)



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
    class Meta:
        model = Ingredient
        fields = ["id", "name", "unit"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.unit")

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", "amount"]


class RecipeListOrRetrieveSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(read_only=True, default=False)

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
        if user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()


################################################################


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipePostOrPatchSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
        return FavoriteRecipe.objects.filter(user=self.context['request'].user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(user=self.context['request'].user, recipe=obj).exists()

    def validate(self, data):
        # Check if ingredients field is empty
        ingredient = set()
        tags = set()
        if not data.get('tags'):
            raise ValidationError({"tags": "Recipe should have at least one tag. d:"})
        for item in data.get('tags'):
            tags.add(item)
        if len(tags) != len(data.get('tags')):
            raise ValidationError({"tags": "unique constraint failed."})

        if not data.get('ingredients'):
            raise ValidationError({"ingredients": "Recipe should have at least one ingredient. d:"})
        for item in data.get('ingredients'):
            ingredient.add(item['id'])
            if item['amount'] < 1:
                raise ValidationError({"ingredients": "Amount value should be greater than 1 or equal. d:"})
        if len(ingredient) != len(data.get('ingredients')):
            raise ValidationError({"ingredients": "unique constraint failed."})
        if data.get('cooking_time') < 1:
            raise ValidationError({"cooking_time": "Should value be greater than 1 or equal. d:"})
        return data

    def create(self, validated_data):
        # Извлечение данных ингредиентов
        ingredients_data = validated_data.pop("ingredients")
        """
        # Реализация сложения повторяющихся ингредиентов.
        # Чисто вириант реализации на будущее.
        # ingredients = dict()
        # data_set = dict()
        # for item in ingredients_data:
        #     if item["id"] in ingredients.keys():
        #         ingredients[item["id"]] += item["amount"]
        #     else:
        #         ingredients[item["id"]] = item["amount"]
        # for id, amount in ingredients.items():
        #     data_set[id] = amount
        """
        recipe = super().create(validated_data)

        # Создание связей с ингредиентами
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data.pop("id")  # Получение объекта ингредиента
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                # amount=ingredient_data['amount']
                **ingredient_data,  # Присвоение остальных полей
            )
        recipe.refresh_from_db()
        return recipe

    def update(self, instance, validated_data):
        # Извлечение данных ингредиентов
        if validated_data.get("ingredients"):
            ingredients_data = validated_data.pop("ingredients")

            for ingredient_data in ingredients_data:
                ingredient_id = ingredient_data.pop("id")  # Получение id ингредиента
                recipe_ingredient, _ = RecipeIngredient.objects.update_or_create(
                    recipe=instance,
                    ingredient_id=ingredient_id,
                    defaults=ingredient_data,  # Присвоение остальных полей
                )
        super().update(instance, validated_data)

        return instance

    def to_representation(self, instance):
        # Customize the output to match the desired schema
        representation = super().to_representation(instance)

        # Modify tags to include `id`, `name`, and `slug`
        representation['tags'] = [
            {'id': tag.id, 'name': tag.name, 'slug': tag.slug} for tag in instance.tags.all()
        ]

        # Modify ingredients to include `id`, `name`, `measurement_unit`, and `amount`
        ingredients = []
        for recipe_ingredient in instance.ingredients.all():
            ingredient = recipe_ingredient.ingredient
            ingredients.append({
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.unit,
                'amount': recipe_ingredient.amount
            })
        representation['ingredients'] = ingredients

        # Modify author to include additional fields
        representation['author'] = {
            'id': instance.author.id,
            'username': instance.author.username,
            'first_name': instance.author.first_name,
            'last_name': instance.author.last_name,
            'email': instance.author.email,
            'is_subscribed': Subscription.objects.filter(user=self.context['request'].user, subscribed_to=instance.author).exists(),  # Example value; change based on your logic
            'avatar': instance.author.avatar.url if instance.author.avatar else None  # Example value; change based on your logic
        }



        return representation


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
    measurement_unit = serializers.CharField(source="unit")
    class Meta:
        model = Ingredient
        fields = ["id", "name", "measurement_unit"]


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ["user", "recipe"]


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="recipe.id")
    image = serializers.ReadOnlyField(source="recipe.image.url")
    name = serializers.ReadOnlyField(source="recipe.name")
    cooking_time = serializers.ReadOnlyField(source="recipe.cooking_time")

    class Meta:
        model = ShoppingCart
        fields = ["id", "image", "name", "cooking_time"]

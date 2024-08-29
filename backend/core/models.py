import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .validators import validate_username


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=settings.MAX_LENGTH_EMAIL,
        verbose_name="Эл. Почта",
    )
    username = models.CharField(
        max_length=settings.MAX_LENGTH_NAME,
        unique=True,
        verbose_name="Имя пользователя",
        validators=[validate_username],
    )
    first_name = models.CharField(
        max_length=settings.MAX_LENGTH_NAME, verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=settings.MAX_LENGTH_NAME, verbose_name="Фамилия"
    )
    avatar = models.ImageField(
        upload_to="users/avatars",
        verbose_name="Фото профиля",
        null=True,
        default=None,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Подписан на",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "subscribed_to")
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} subscribed to {self.subscribed_to}"


class Tag(models.Model):
    name = models.CharField(
        max_length=50, unique=True, verbose_name="Название"
    )
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Слаг")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Название"
    )
    measurement_unit = models.CharField(
        max_length=50, unique=False, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Игредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=100, verbose_name="Название")
    image = models.ImageField(
        upload_to="recipes/images/", verbose_name="Изображение"
    )
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления"
    )
    tags = models.ManyToManyField(
        Tag, related_name="recipes", verbose_name="Теги"
    )

    class Meta:
        unique_together = ("author", "name")
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name

    def is_favorited_by(self, user):
        return FavoriteRecipe.objects.filter(user=user, recipe=self).exists()

    def is_in_shopping_cart_by(self, user):
        return ShoppingCart.objects.filter(user=user, recipe=self).exists()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(verbose_name="Кол-во")

    class Meta:
        unique_together = ("recipe", "ingredient")
        verbose_name = "Игредиент Рецепта"
        verbose_name_plural = "Игредиенты Рецептов"

    def __str__(self):
        return (
            f"{self.amount} {self.ingredient.measurement_unit} "
            f"of {self.ingredient.name} in {self.recipe.name}"
        )


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


class ShortenedRecipeURL(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shortened_url",
        verbose_name="Рецепт",
    )
    short_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_short_code,
        verbose_name="Код",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Время создания"
    )

    class Meta:
        verbose_name = "Короткая ссылка"
        verbose_name_plural = "Короткие ссылки"

    def __str__(self):
        return f"{self.short_code} -> {self.recipe.name}"


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_recipes",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Рецепт",
    )
    added_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Время добавления"
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "Список Избранного"
        verbose_name_plural = "Списки избранного"

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart_recipes",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart_by",
        verbose_name="Рецепт",
    )
    added_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Время добавления"
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"{self.user.username} -> " f"{self.recipe.name}"

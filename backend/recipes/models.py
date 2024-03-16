from django.contrib.auth import get_user_model
from django.core.validators import (
    MinValueValidator, MaxValueValidator, RegexValidator)
from django.db import models

User = get_user_model()


MIN_NUMBERS = 1
MAX_NUMBERS = 32000


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        help_text=('Цвет в должен быть в формате HEX, например: #49B64E.'),
        validators=(
            RegexValidator(
                regex=r'^#[a-fA-F0-9]{6}$',
                message='Цвет должен быть в формате HEX.',
                code='wrong_hex_code',
            ),
        ),
        default='#ffffff'
    )
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=100,
        help_text='Введите слаг тега',
        unique=True
    )

    class Meta:
        verbose_name = 'Tег'
        verbose_name_plural = 'Tеги'
        ordering = ('-pk',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'slug'),
                name='unique_name_slug'
            )
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=200,
        db_index=True,
    )
    measurement_unit = models.CharField(
        verbose_name='Еденица измерения',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('-pk',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        db_index=True,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='foodgram_backend/images/',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipe',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления.',
        validators=[
            MinValueValidator(
                MIN_NUMBERS,
                message='Время приготовления должно быть '
                        'не меньше одной минуты.'),
            MaxValueValidator(
                MAX_NUMBERS,
                message='Время приготовления должно быть '
                        'не больше 32000 минут')
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_NUMBERS, message='Количество должно быть больше нуля.'
            ),
            MaxValueValidator(
                MAX_NUMBERS, message='Количество должно быть меньше 32000.')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        ordering = ['pk']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient_pair',
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorite',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorite',
    )
    date_added: models.DateTimeField = models.DateTimeField(
        verbose_name='дата создания',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        ordering = ('-date_added',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]

    def __str__(self):
        return (f'{self.user.username} добавил '
                f'{self.recipe.name} в избранное.')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('pk',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return (f'{self.user.username} добавил '
                f'{self.recipe.name} в список покупок.')

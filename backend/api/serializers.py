import base64
import imghdr

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import AuthenticationFailed

from recipes.models import (
    Favorite, Ingredient, IngredientAmountForRecipe,
    Recipe, ShoppingCart, Tag
)
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    """Декодирует картинку из строки base64."""

    def to_internal_value(self, data):
        """Преобразует строку base64 в объект ContentFile."""
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                image_data = base64.b64decode(imgstr)
                ext = imghdr.what(None, h=image_data)
                if not ext:
                    raise serializers.ValidationError(
                        "Некорректное изображение"
                    )
                name = f'{self.context["request"].user.username}.{ext}'
                return ContentFile(image_data, name=name)
            except Exception:
                raise serializers.ValidationError(
                    "Ошибка при обработке изображения"
                )
        return super().to_internal_value(data)


class UserMeSerializer(UserSerializer):
    """Сериализатор me пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def to_representation(self, instance):
        if self.context['request'].user.is_anonymous:
            raise AuthenticationFailed("Вы не аутентифицированы.")
        return super().to_representation(instance)

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь
        на указанного пользователя.
        """
        user = self.context.get('request').user
        return (
            user.followers.filter(author=obj).exists()
            if user.is_authenticated else False
        )


class UserDetailSerializer(UserSerializer):
    """Сериализатор для детального представления пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь
        на указанного пользователя.
        """
        user = self.context.get('request').user
        return (
            user.followers.filter(author=obj).exists()
            if user.is_authenticated else False
        )


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор регистрации пользователя."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email'],
            )
        ]


class FollowSerializer(UserDetailSerializer):
    """Сериализатор для подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count'
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = ('recipes', 'recipes_count')

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author',)
            )
        ]

    def get_recipes(self, obj):
        """Получает список рецептов для пользователя."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeShortSerializer(recipes, many=True).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientAmountForRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientAmountForRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipesListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    tags = TagSerializer(many=True)
    author = UserDetailSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date', )
        read_only_fields = (
            'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_ingredients(self, obj):
        """Получает список ингредиентов."""
        queryset = obj.ingredient_amount.all()
        return IngredientAmountForRecipeSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.favorite_recipe.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет,
        добавлены ли ингредиенты этого рецепта в Список покупок.
        """
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.recipe_in_cart.filter(recipe=obj).exists()
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецепта."""
    ingredients = IngredientAmountForRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate_tags(self, tags):
        """
        Проверяет, что теги в запросе не повторяются.
        """
        unique_tags = set(tags)
        if len(tags) != len(unique_tags):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return tags

    def validate(self, attrs):
        """
        Валидация данных перед созданием или обновлением рецепта.
        Проверяет входные данные, такие как ингредиенты и их количество,
        а также форматирует текстовое поле и название рецепта.
        """
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                "Ингредиенты обязательны для обновления рецепта."
            )

        # Проверка, что в запросе есть теги
        tags = attrs.get('tags')
        if not tags:
            raise serializers.ValidationError(
                "Теги обязательны для обновления рецепта."
            )

        ingredients = self.initial_data.get('ingredients')
        validated_ingrediets = []
        unique_ingredients_id = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    {'Ингредиент':
                     f'Не существующий ингредиент: {ingredient_id}'}
                )

            if ingredient_id in unique_ingredients_id:
                raise serializers.ValidationError(
                    {'Ингредиент': 'Ингредиенты не должны повторяться.'}
                )
            unique_ingredients_id.append(ingredient_id)

            ingredient_count = int(ingredient.get('amount'))
            if ingredient_count < 1:
                raise serializers.ValidationError(
                    {'Ингредиент':
                     'Количество ингредиентов должно быть больше '
                     'или равно 1.'}
                )
            validated_ingrediets.append(
                {'id': ingredient_id, 'amount': ingredient_count}
            )

        text_in_list: list[str] = list(self.initial_data.get('text'))
        text_in_list[0] = text_in_list[0].capitalize()
        text: str = ''.join(text_in_list)

        attrs['ingredients'] = validated_ingrediets
        attrs['name'] = str(self.initial_data.get('name')).capitalize()
        attrs['text'] = text

        return attrs

    def _set_amount_to_ingredient(self, recipe, ingredients):
        """Создат связь между рецептом и ингредиентом."""
        for ingredient in ingredients:
            IngredientAmountForRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount')
            )

    @transaction.atomic
    def create(self, validated_data):
        """Создает новый рецепт."""
        validated_data['author'] = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._set_amount_to_ingredient(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        recipe = instance

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)
        if ingredients:
            recipe.ingredients.clear()
            self._set_amount_to_ingredient(recipe, ingredients)

        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        """Преобразует объект рецепта в формат для отображения."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipesListSerializer(instance, context=context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Тоже сериализатор для рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""
    class Meta:
        model = Favorite
        fields = '__all__'

    def validate(self, attrs):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        if user.favorite_recipe.filter(recipe=attrs.get('recipe')).exists():
            raise serializers.ValidationError(
                {'error': 'Данный рецепт уже добавлен в избранное.'}
            )
        return attrs

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def validate(self, attrs):
        user = self.context.get('request').user
        if user.recipe_in_cart.filter(recipe=attrs.get('recipe')).exists():
            raise serializers.ValidationError(
                {'error': 'Данный рецепт уже добавлен в список покупок.'}
            )
        return attrs

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': request}
        ).data

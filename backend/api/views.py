from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.http.response import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import (
    generics, permissions, response,
    status, viewsets
)
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow, User

from .filters import IngredientSearchFilter, RecipeFilter
from .paginations import CustomPagination
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (
    FollowSerializer, UserDetailSerializer, FavoriteSerializer,
    IngredientAmountForRecipe, IngredientSerializer, RecipeSerializer,
    RecipesListSerializer, ShoppingCartSerializer, TagSerializer,
    UserMeSerializer
)
from .utils import get_shopping_cart_footer


class UserListViewSet(UserViewSet):
    """Вьюсет для отображения списка пользователей."""
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = LimitOffsetPagination


class UserMeViewSet(UserViewSet):
    """Вьюсет для отображения /me/."""
    queryset = User.objects.all()
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user


class FollowListViewSet(generics.ListAPIView):
    """Apiview для отображения списка подписок."""
    serializer_class = FollowSerializer
    pagination_class = CustomPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(
            following__user=self.request.user
        ).annotate(recipes_count=Count('recipes'))


class FollowCreateDestroyViewSet(
    generics.CreateAPIView,
    generics.DestroyAPIView
):
    """Apiview для создания и удаления подписок."""
    serializer_class = FollowSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Обработка HTTP-запроса методом POST для создания подписки."""
        user_id = self.kwargs.get('user_id')
        if user_id == request.user.id:
            return response.Response(
                'Нельзя подписаться на себя самого.',
                status=status.HTTP_400_BAD_REQUEST
            )
        if Follow.objects.filter(
            user=request.user,
            author_id=user_id
        ).exists():
            return response.Response(
                'Вы уже подписаны на данного автора.',
                status=status.HTTP_400_BAD_REQUEST
            )
        author = get_object_or_404(User, id=user_id)
        Follow.objects.create(user=request.user, author_id=user_id)
        return response.Response(
            self.serializer_class(author, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """Обработка HTTP-запроса методом DELETE для удаления подписки."""
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        follow = Follow.objects.filter(
            user=request.user,
            author=user
        )
        if follow:
            follow.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(
            'Вы не подписаны на данного автора.',
            status=status.HTTP_400_BAD_REQUEST
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('$name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipesListSerializer
        return RecipeSerializer

    def create(self, request, *args, **kwargs):
        ingredients_data = request.data.get('ingredients', [])

        if not ingredients_data:
            return response.Response(
                {'error': 'Список ингредиентов не может быть пустым.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            recipe = serializer.save(author=request.user)
            for ingredient_data in ingredients_data:
                headers = self.get_success_headers(serializer.data)
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @transaction.atomic
    def _create_action(self, request, pk, serializer):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @transaction.atomic
    def _delete_action(self, request, pk, klass):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        try:
            obj = klass.objects.get(user=user, recipe=recipe)
        except klass.DoesNotExist:
            return response.Response(
                {'error': f'{klass.__name__} not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST'], detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        """Добавляет рецепт в избранное."""
        return self._create_action(
            request=request, pk=pk, serializer=FavoriteSerializer
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаляет рецепт из избранного."""
        return self._delete_action(request=request, pk=pk, klass=Favorite)

    @action(
        methods=['POST'], detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        """Добавляет рецепт в список покупок."""
        return self._create_action(
            request=request, pk=pk, serializer=ShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаляет рецепт из списка покупок."""
        return self._delete_action(
            request=request, pk=pk, klass=ShoppingCart
        )

    @action(
        methods=['GET'], detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def download_shopping_cart(self, request):
        """Загружает список покупок в виде текстового файла."""
        user = self.request.user
        if not user.recipe_in_cart.exists():
            return {}
        '''
            raise serializers.ValidationError({
                'error': 'В списке покупок нет ни одного рецепта.'
            })'''

        recipe_id_list = user.recipe_in_cart.values_list('recipe_id')
        ingredients_in_cart = IngredientAmountForRecipe.objects.filter(
            recipe__in=recipe_id_list
        ).values_list(
            'ingredient__name',
            'ingredient__measurement_unit',
            'amount'
        )

        ingredients = {}
        for (name, measurement_unit, amount) in ingredients_in_cart:
            if name not in ingredients:
                ingredients[name] = {
                    'name': name,
                    'measurement_unit': measurement_unit,
                    'amount': amount
                }
            else:
                ingredients[name]['amount'] += amount

        shopping_cart_out = 'Ваш список покупок:\n'
        for ingredient in ingredients.values():
            shopping_cart_out += '\u00B7 {} ({}) \u2014 {}\n'.format(
                ingredient['name'].capitalize(),
                ingredient['measurement_unit'],
                ingredient['amount']
            )
        shopping_cart_out += get_shopping_cart_footer()

        response = HttpResponse(
            shopping_cart_out, content_type='text/plain; charset=utf-8'
        )

        filename = str(user) + '-shopping-list' + '.txt'
        response['Content-Disposition'] = (
            f'attachment; filename={filename}'
        )
        return response

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated

)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from recipes.models import (
    Ingredient, Tag, Recipe, FavoriteRecipe, ShoppingList, Follow,
    ListOfIngredients, ListOfTags
)
from users.models import User
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer, CustomUserSerializer, CustomCreateUserSerializer,
    FollowSerializer, AddFavoritesSerializer, IngredientInRecipeSerializer,
    CreateIngredientsInRecipeSerializer, RecipeCreateUpdateSerializer,
    RecipeDetailSerializer, FavoriteRecipeSerializer,
)


class Pagination(PageNumberPagination):
    """Paging for the RecipeViewSet."""
    
    page_size_query_param = 'limit'
    page_size = 6


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет работы с обьектами класса Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с обьектами класса Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)

    @action(
        detail=False,
        methods=('get',),
        url_path='search',
        url_name='search',
    )
    def search(self, request):
        """Метод для поиска ингредиентов по названию."""
        query_param = request.query_params.get('name', '').strip()
        if not query_param:
            return Response({'error': 'Пожалуйста, укажите название ингредиента.'}, status=status.HTTP_400_BAD_REQUEST)

        ingredients = Ingredient.objects.filter(name__icontains=query_param)
        serializer = self.get_serializer(ingredients, many=True)
        return Response(serializer.data)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с обьектами класса User и подписки на авторов."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = Pagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated, ),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Метод для создания страницы подписок"""

        queryset = User.objects.filter(follow__user=self.request.user)
        if queryset:
            pages = self.paginate_queryset(queryset)
            serializer = FollowSerializer(pages, many=True,
                                          context={'request': request})
            return self.get_paginated_response(serializer.data)
        return Response('Вы ни на кого не подписаны.',
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Метод для управления подписками """

        user = request.user
        author = get_object_or_404(User, id=id)
        change_subscription_status = Follow.objects.filter(
            user=user.id, author=author.id
        )
        if request.method == 'POST':
            if user == author:
                return Response('Вы пытаетесь подписаться на себя!!',
                                status=status.HTTP_400_BAD_REQUEST)
            if change_subscription_status.exists():
                return Response(f'Вы теперь подписаны на {author}',
                                status=status.HTTP_400_BAD_REQUEST)
            subscribe = Follow.objects.create(
                user=user,
                author=author
            )
            subscribe.save()
            return Response(f'Вы подписались на {author}',
                            status=status.HTTP_201_CREATED)
        if change_subscription_status.exists():
            change_subscription_status.delete()
            return Response(f'Вы отписались от {author}',
                            status=status.HTTP_204_NO_CONTENT)
        return Response(f'Вы не подписаны на {author}',
                        status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(ModelViewSet):
    """ViewSet для обработки запросов, связанных с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = Pagination
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        """Метод для вызова определенного сериализатора. """

        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        elif self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer

    def get_serializer_context(self):
        """Метод для передачи контекста. """

        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Метод для управления избранными подписками """

        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': f'Повторно - \"{recipe.name}\" добавить нельзя,'
                               f'он уже есть в избранном у пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = AddFavoritesSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            obj = FavoriteRecipe.objects.filter(user=user, recipe=recipe)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': f'В избранном нет рецепта \"{recipe.name}\"'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки ингредиентов и их количества
         для выбранных рецептов"""

        user = request.user
        ingredients = ListOfIngredients.objects.filter(
            recipe__shopping_recipe__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))

        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )

        return HttpResponse(shopping_list, content_type='text/plain')

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Метод для объединения ингредиентов в список для загрузки"""

        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_favorite_shopping_cart',
        url_name='download_favorite_shopping_cart',
    )
    def download_favorite_shopping_cart(self, request):
        """Метод для загрузки ингредиентов и их количества
         для избранных рецептов"""

        ingredients = ListOfIngredients.objects.filter(
            recipe__favorites__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('quantity'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки ингредиентов и их количества
         для выбранных рецептов"""

        ingredients = ListOfIngredients.objects.filter(
            recipe__shopping_list__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('quantity'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')
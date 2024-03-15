from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def is_anonymous_or_in_db(self, queryset, name, value, related_field):
        if self.request.user.is_anonymous:
            return Recipe.objects.none() if value else queryset
        objects = getattr(
            self.request.user, related_field
        ).all()
        return queryset.filter(
            pk__in=objects.values_list('recipe__pk', flat=True)
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return (
            self.is_anonymous_or_in_db
            (queryset, name, value, 'shopping_cart'))

    def filter_is_favorited(self, queryset, name, value):
        return (
            self.is_anonymous_or_in_db
            (queryset, name, value, 'favourite'))

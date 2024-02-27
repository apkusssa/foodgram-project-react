from django.contrib import admin

from recipes.models import (
    Favorite, Ingredient, IngredientAmountForRecipe,
    Recipe, ShoppingCart, Tag
)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', )


class IngredientInline(admin.StackedInline):
    model = IngredientAmountForRecipe
    extra = 0


@admin.register(IngredientAmountForRecipe)
class IngredientAmountForRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', )
    search_fields = ('ingredient__name', 'recipe__name')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInline, )
    fields = (
        'author',
        'name',
        'image',
        'text',
        'ingredient_inline',
        'tags',
        'cooking_time'
    )

    list_display = ('name', 'author', 'amount_favorite')
    list_filter = ('author', 'name', 'tags')
    search_fields = ('author__username', 'name__icontains')

    readonly_fields = ('ingredient_inline', )

    @admin.display(description='Ингредиенты')
    def ingredient_inline(self, *args, **kwargs):
        from django.template.loader import get_template
        context = getattr(self.response, 'context_data', None) or {}
        context['inline_admin_formset'] = (
            context['inline_admin_formsets'].pop(0)
        )
        inline = context['inline_admin_formset']
        return get_template(inline.opts.template).render(context, self.request)

    def render_change_form(self, request, *args, **kwargs):
        self.request = request
        self.response = super().render_change_form(request, *args, **kwargs)
        return self.response

    @admin.display(description='Количество в избранном')
    def amount_favorite(self, obj):
        amount = Favorite.objects.filter(recipe=obj).count()
        return amount


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('slug', )
    list_filter = ('slug', )
    search_fields = ('slug', )

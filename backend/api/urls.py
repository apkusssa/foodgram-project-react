from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, IngredientsVewSet, RecipeViewSet,
                    TagsViewSet)

app_name = 'api'

router: DefaultRouter = DefaultRouter()
router.register('tags', TagsViewSet)
router.register('recipes', RecipeViewSet)
router.register('users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientsVewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

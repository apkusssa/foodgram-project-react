from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet,
    FollowCreateDestroyViewSet, FollowListViewSet, UserListViewSet,
    UserMeViewSet
)

router = DefaultRouter()

router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserListViewSet, basename='users')
router.register(r'users/me/', UserMeViewSet, basename='user-me')

urlpatterns = [
    path(
        'users/subscriptions/',
        FollowListViewSet.as_view(),
        name='subscriptions'
    ),
    path(
        'users/<int:user_id>/subscribe/',
        FollowCreateDestroyViewSet.as_view(),
        name='subscribe'
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

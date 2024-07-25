from django.urls import path
from .views import RecipeCreateAPIView, RecipeListAPIView, RecipeDetailAPIView, RecipeCategoryAPIView, RecipeSearchAPIView, LikeAPIView

urlpatterns = [
path('recipes/', RecipeCreateAPIView.as_view(), name='recipe-create'),
path('main/', RecipeListAPIView.as_view(), name='main-page'),
path('recipes/int:pk/', RecipeDetailAPIView.as_view(), name='recipe-detail'),
path('recipes/category/str:category', RecipeCategoryAPIView.as_view(), name='recipe_category'),
path('recipes/search/', RecipeSearchAPIView.as_view(), name='recipe_search'),
path('recipes/int:recipe_id/like/', LikeAPIView.as_view(), name='like-recipe')
]
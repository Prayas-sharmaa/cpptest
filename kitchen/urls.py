from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/create/', views.create_order, name='create_order'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.add_inventory, name='add_inventory'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/add/', views.add_recipe, name='add_recipe'),
    path("inventory/edit/<str:item_id>/", views.edit_inventory, name="edit_inventory"),
    path("recipes/edit/<str:recipe_id>/", views.edit_recipe, name="edit_recipe"),

]

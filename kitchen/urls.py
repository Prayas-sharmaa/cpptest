from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Orders
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/delete/<str:order_id>/', views.delete_order, name='delete_order'),

    # Inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.add_inventory, name='add_inventory'),
    path('inventory/edit/<str:item_id>/', views.edit_inventory, name='edit_inventory'),
    path('inventory/delete/<str:item_id>/', views.delete_inventory, name='delete_inventory'),

    # Recipes
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/add/', views.add_recipe, name='add_recipe'),
    path('recipes/edit/<str:recipe_id>/', views.edit_recipe, name='edit_recipe'),
    path('recipes/delete/<str:recipe_id>/', views.delete_recipe, name='delete_recipe'),
]


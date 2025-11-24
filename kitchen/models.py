from django.db import models

class Order(models.Model): #  Represents a customer order placed in the Cloud Kitchen system.
    order_id = models.CharField(max_length=100, primary_key=True)
    recipe = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='PENDING')

class InventoryItem(models.Model): #epresents a single inventory item stored inside the kitchen.
    item_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    qty = models.IntegerField()

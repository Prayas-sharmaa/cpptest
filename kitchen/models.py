from django.db import models

class Order(models.Model):
    order_id = models.CharField(max_length=100, primary_key=True)
    recipe = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='PENDING')

class InventoryItem(models.Model):
    item_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)
    qty = models.IntegerField()

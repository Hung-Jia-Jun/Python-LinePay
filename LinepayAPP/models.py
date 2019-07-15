from django.db import models

class shoppingCart(models.Model):
    member = models.ForeignKey('member')
    shopId = models.TextField()
    itemName = models.TextField()
    itemPrice = models.IntegerField()
    addOnNameHistory = models.TextField()
    addOnPriceHistory = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

class clientSession(models.Model):
    status = models.TextField(default = 'default')
    member = models.ForeignKey('member')
    updated_at = models.DateTimeField(auto_now=True)

class member(models.Model):
    lineID = models.TextField()
    displayName = models.TextField()
    address = models.TextField()
    phone = models.TextField()
    birthDay = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    

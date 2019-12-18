from django.db import models
import uuid

class shoppingCart(models.Model):
    member = models.ForeignKey('member',on_delete=models.CASCADE)
    shopId = models.TextField()
    itemClassId = models.TextField()
    itemClassName = models.TextField()
    itemName = models.TextField()
    itemPrice = models.IntegerField()
    addOnNameHistory = models.TextField()
    addOnPriceHistory = models.TextField()
    totalPrice = models.IntegerField(default = 0)
    isPayed = models.TextField(default='False')
    updated_at = models.DateTimeField(auto_now=True)
    isTaked = models.BooleanField(default=False)
    productAmount = models.IntegerField(default = 0)
    productImage = models.TextField()
    linkOrderId = models.TextField()
    inviteCode = models.TextField()
    cashOnDelivery = models.BooleanField(default=False)
    
class systemSetting(models.Model):
    inviteCodeStatus = models.TextField(default='0')
    autoReGeneratorInviteCode = models.TextField(default='True')
    saleNumber = models.IntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

class clientSession(models.Model):
    status = models.TextField(default = '')
    member = models.ForeignKey('member',on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

class inviteCodeManager(models.Model):
    owner = models.ForeignKey('member',on_delete=models.CASCADE)
    user = models.ForeignKey(to = 'member' , related_name = 'user_member',on_delete=models.CASCADE, null=True, blank=True)
    code = models.TextField(default='')
    status = models.TextField(default='')
    updated_at = models.DateTimeField(auto_now=True)

class member(models.Model):
    lineID = models.TextField()
    displayName = models.TextField()
    address = models.TextField()
    phone = models.TextField()
    birthDay = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    orderId = models.TextField(default= '')
    recommendHistory = models.TextField(default= '')
class testLog(models.Model):
    message = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

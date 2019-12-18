from django.conf.urls import url
from LinepayAPP.views import *
import django
import os
urlpatterns = [
    url(r'^callback/$', callback),
    url(r'^confirm/$', confirm),
    url(r'^settingInviteCode/$', settingInviteCode),
    url(r'^queryOrderByCode/$', queryOrderByCode),
    url(r'^setIsTakeOrderByCode/$', setIsTakeOrderByCode),
    url(r'^queryAllOrder/$', queryAllOrder),
    
]

from django.conf.urls import url
from LinepayAPP.views import *


urlpatterns = [
    url(r'^callback/$', callback),
    url(r'^confirm/$', confirm),
]
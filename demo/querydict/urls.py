from django.conf.urls import re_path
from . import views


urlpatterns = [
            re_path(r'getquerydict/$', views.getquerydict),
            re_path(r'postquerydict/$', views.postquerydict),
        ]

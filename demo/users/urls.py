from django.conf.urls import re_path
from . import views


app_name = 'us'


urlpatterns  = [
        re_path(r'index/$', views.index, name='index'),
        re_path(r'sayhello/$', views.sayhello, name='sayhello'),
        re_path(r'say/$', views.say, name='say'),
        ]

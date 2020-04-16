from django.conf.urls import re_path
from . import views


urlpatterns = [
        re_path(r'name/([a-zA-Z]+)/age/(\d{2})$', views.message),
        
        ]

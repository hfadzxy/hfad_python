from django.conf.urls import re_path
from . import views




urlpatterns  = [
    re_path(r'^db_book/$', views.SaveDataView.as_view()),
    re_path(r'^func/$', views.func)
        ]

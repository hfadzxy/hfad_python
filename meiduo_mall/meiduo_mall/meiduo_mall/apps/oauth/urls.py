from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^qq/authorization/$', views.QQURLView.as_view()),
    re_path(r'^oauth_callback/$', views.QQUserView.as_view()),
]
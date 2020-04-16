from django.urls import re_path
from django.views import View
from . import views

urlpatterns = [
    re_path(r'username/(?P<username>[0-9a-zA-Z_-]{5,20})/count/$', views.UsernameCountView.as_view()),
]
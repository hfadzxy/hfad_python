from django.urls import re_path
from django.views import View
from . import views

urlpatterns = [
    re_path(r'^carts/$', views.CartsView.as_view()),
]
from django.urls import re_path
from . import views


urlpatterns = [
    re_path(r'^mixin1/$', views.Mixin1.as_view()),
]


from django.urls import re_path
from . import views


urlpatterns = [
    re_path(r'^class1/$', views.Classview1.as_view()),
    re_path(r'^class2/$', views.my_decorator(views.Classview2.as_view())),
    re_path(r'^class3/$', views.Classview3.as_view()),
    re_path(r'^class4/$', views.Classview4.as_view()),
]

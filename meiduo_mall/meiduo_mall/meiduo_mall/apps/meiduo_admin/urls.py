from django.urls import re_path
from meiduo_admin.views import statistical
from rest_framework_jwt.views import obtain_jwt_token
# obtain_jwt_token 就是后台登录借口, 返回token
urlpatterns = [
    re_path(r'^authorizations/$', obtain_jwt_token),
    re_path(r'^statistical/total_count$', statistical.UserTotalCountView.as_view()),

]

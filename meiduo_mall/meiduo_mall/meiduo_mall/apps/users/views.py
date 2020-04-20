from django.shortcuts import render
from django.views import View
from users.models import User
from django.http import JsonResponse

# Create your views here.
class UsernameCountView(View):
    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
            print(count)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'访问数据库失败'})

        return JsonResponse({'code':0, 'errmsg':'ok', 'count':count})


class MobileCountView(View):
    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'访问数据库出错'})

        return JsonResponse({'code':0, 'errmsg':'ok', 'count':count})




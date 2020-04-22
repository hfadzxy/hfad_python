from django.contrib.auth import login, authenticate
from django.shortcuts import render
from django_redis import get_redis_connection
import re
import json
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


class RegisterView(View):
    def post(self, request):
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')
        # 检测全部参数是否全
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return JsonResponse({'code':404, 'errmsg':'缺少必传参数'})

        # username 检测
        if not re.match(r'[a-zA-Z_-]{5,20}$', username):
            return JsonResponse({'code':404, 'errmsg':'username格式错误'})

        # password 检测
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return JsonResponse({'code':404, 'errmsg':'password格式错误'})
        if password2 != password:
            return JsonResponse({'code':404, 'errmsg':'两次输入不对'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return  JsonResponse({'code':400, 'errmsg':'mobile格式错误'})

        if allow != True:
            return JsonResponse({'code':400, 'errmsg':'allow格式错误'})

        # 检测sms_code
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'code':400, 'errmsg':'短信验证码过期'})
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code':400,'errmsg':'验证码有误'})
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'保存到数据库'})

        # 实现状态保持
        login(request, user)

        return JsonResponse({'code':0, 'errmsg':'ok'})


class LoginView(View):
    def post(self, request):
        # 接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')
        # 检测参数是否全
        if not all([username, password]):
            return JsonResponse({'code':400, 'errmsg':'缺少参数'})

        # 验证是否登录,返回布尔
        user = authenticate(username=username, password=password)

        # 判断是否为空
        if user is None:
            return JsonResponse({'code':400, 'errmsg':'用户名或密码错误'})

        # 状态保持
        login(request, user)

        # 判断是否记住用户
        if remembered != True:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)


        # 返回cookie 用户名
        response = JsonResponse({'code':0, 'errmsg':'ok'})
        response.set_cookie('username', user.username, max_age=3600*24*14)

        # 返回json
        return response


































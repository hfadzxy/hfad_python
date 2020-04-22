import json
import re

from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.http import JsonResponse
# 工程设置文件导入， 规定写法
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from django.views import View
import logging

from django_redis import get_redis_connection

from oauth.models import QAuthQQUser
from oauth.utils import generate_access_token_by_openid, check_access_token
from users.models import User

logger = logging.getLogger('django')

class QQURLView(View):
    def get(self, request):
        # 1. 接受查询字符串参数
        next = request.GET.get('next')
        # 2. 用QQLoginTool工具类创建对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                client_secret=settings.QQ_CLIENT_SECRET,
                redirect_uri=settings.QQ_REDIRECT_URI,
                state=next)
        # 3. 利用对象，调用函数， 获取qq登录的地址
        url = oauth.get_qq_url()
        # 4. 返回json(code, errmsg, login_rul)
        return JsonResponse({'code':0, 'errmsg':'ok','login_url':url})


class QQUserView(View):
    def get(self, request):
        # 1. 获取code
        code = request.GET.get('code')
        # 2. 判断code是否存在
        if not code:
            return JsonResponse({'code':400, 'errmsg':'缺少code参数'})
        # 3. 调用QQLoginTool工具类，创建工具对象

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 4.携带code向QQ服务器，请求access_token
            access_token = oauth.get_access_token(code)
            # 5.携带access_token 向QQ服务器， 请求openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            # 6.如果4， 5 错误， 报错
            logger.error(e)
            # 7. 返回结果
            return JsonResponse({'code':400, 'errmsg':'oauth2.0认证失败， 即获取qq信息失败'})

        # 8. 根据openid， 在QQ表获取对饮的对象
        try:
            oauth_qq = QAuthQQUser.objects.get(openid=openid)

        except Exception as e:
            # 封装一个函数: 把openid加密access_token
            access_token = generate_access_token_by_openid(openid)
            # 返回code不要为0， 前端设置为0返回首页
            return JsonResponse({'code':300, 'errmsg':'ok', 'access_token':access_token})

        else:
            # 9. 如果该对象获取到了， 登录成功
            user = oauth_qq.user
            # 10.实现状态保持
            login(request, user)
            response = JsonResponse({'code':0, 'errmsg':'ok'})
            response.set_cookie('username', user.username, max_age=3600*24*14)
            return response

    def post(self, request):
        '''qq登录的第三个接口'''
        # 接收参数（json）
        dict = json.loads(request.body.decode())
        mobile = dict.get('mobile')
        password = dict.get('password')
        sms_code_client = dict.get('sms_code')
        access_token = dict.get('access_token')

        # 总体检测，查看是否有空
        if not all([mobile, sms_code_client, password, access_token]):
            return JsonResponse({'code':400, 'errmsg':'缺少必传参数'})

        # mobile检测
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code':400, 'errmsg':'mobile格式有误'})

        # password 检测
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return JsonResponse({'code':400, 'errmsg':'密码格式错误'})

        # 链接redis, 获取redis的连接对象
        redis_conn = get_redis_connection('verify_code')

        # 获取短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断短信验证码是否为空
        if sms_code_server is None:
            return JsonResponse({'code':400, 'errmsg':'短信验证码过期'})

        # 对比前后端短信验证码
        if sms_code_client.lower() != sms_code_server.decode().lower():
            return JsonResponse({'code':400, 'errmsg':'输入短信验证码有误'})

        # 定义函数， 解密access_token
        openid = check_access_token(access_token)

        # 判断openid 是否存在
        if openid is None:
            return JsonResponse({'code':400, 'errmsg':'openid为空'})

        # 从User表中获取一个该手机号对应的用户
        try:
            user = User.objects.get(mobile=mobile)

        # 如果该用户不存在， 添加用户
        except Exception as e:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

        # 用户存在， 比较密码
        else:
            if not user.check_password(password):
                return JsonResponse({'code':400, 'errmsg':'密码输入不对'})

        # 保存openid 和 user 到QQ表
        try:
            QAuthQQUser.objects.create(openid=openid, user=user)

        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'保存qq表中出错 '})

        # 保持状态
        login(request, user)

        # 创建响应对象
        response = JsonResponse({'code':0, 'errmsg':'ok'})

        # 登录用户名写入cookie
        response.set_cookie('username', user.username, max_age=3600*24*14)
        return response

        #





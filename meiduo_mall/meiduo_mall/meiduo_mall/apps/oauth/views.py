from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.http import JsonResponse
# 工程设置文件导入， 规定写法
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from django.views import View
import logging

from oauth.models import QAuthQQUser
from oauth.utils import generate_access_token_by_openid

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






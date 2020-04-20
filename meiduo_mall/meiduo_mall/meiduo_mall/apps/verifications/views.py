from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection


# Create your views here.
class ImageCodeView(View):
    def get(self, request, uuid):
        # 1. 调用工具类captcha 生成图片验证码
        text, image = captcha.generate_captcha()
        # 2. 链接redis, 获取连接对象
        redis_conn = get_redis_connection('verify_code')
        # 3. 利用链接对象，保存数据到redis， 使用setex函数
        redis_conn.setex('img_%s' % uuid, 300, text)
        # 4. 返回图片
        return HttpResponse(image, content_type='image/jpg')




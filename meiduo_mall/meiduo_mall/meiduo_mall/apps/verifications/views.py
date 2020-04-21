from django.shortcuts import render
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
import random
import logging
logger = logging.getLogger('django')
from django.views import View
from django.http import HttpResponse, JsonResponse
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

# class SMSCodeView(View):
#     def get(self, request, mobile):
#         redis_conn = get_redis_connection('verify_code')
#         send_flag = redis_conn.get('send_flag_%s' % mobile)
#         if send_flag:
#             return JsonResponse({'code':400, 'errmsg':'发送短信过于频繁'})
#
#         # 接受参数
#         image_code_client = request.GET.get('image_code')
#         uuid = request.GET.get('image_code_id')
#
#         # 校验参数, 验证参数是否全
#         if not all([image_code_client, uuid]):
#             return JsonResponse({'code':400, 'errmsg':'缺少必要参数'})
#
#         # redis 中提取参数
#         # 链接redis
#         redis_conn = get_redis_connection('verify_code')
#         # 获取redis中的验证码
#         image_code_server = redis_conn.get('img_%s' % uuid)
#         # 如果redis中没有对应验证码， 说明验证码失效
#         if image_code_server is None:
#             return JsonResponse({'code':400, 'errmsg':'图形验证码失效'})
#         # 如果提取出验证码， 提前删除，避免在有效期内测试验证码
#         try:
#             redis_conn.delete('img_%s' % uuid)
#         except Exception as e:
#             logger.error(e)
#
#         # 对比验证码, redis 中的数据是bytes字节, 需要转码
#         image_code_server = image_code_server.decode()
#         # 转为小写比较
#         if image_code_server.lower() != image_code_client.lower():
#             return JsonResponse({'code':400, 'errmsg':'输入图形有误'})
#         # 如果验证码有效， 生成短信验证码
#         sms_code = '%06d' % random.randint(0,999999)
#         redis_conn.setex('sms_%s' % mobile,300, sms_code)
#
#         # 发送短信验证码
#         redis_conn.setex('send_flag_%s' % mobile, 60, 1)
#         CCP().send_template_sms(mobile,[sms_code, 5], 1)
#
#         # 返回相应结果
#         return JsonResponse({'code':0, 'errmsg':'发送短信成功'})


# 建立pipeline操作redis管道
class SMSCodeView(View):
    def get(self, request, mobile):
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return JsonResponse({'code':400, 'errmsg':'发送短信过于频繁'})

        # 接受参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 校验参数, 验证参数是否全
        if not all([image_code_client, uuid]):
            return JsonResponse({'code':400, 'errmsg':'缺少必要参数'})

        # redis 中提取参数
        # 链接redis
        redis_conn = get_redis_connection('verify_code')
        # 获取redis中的验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        # 如果redis中没有对应验证码， 说明验证码失效
        if image_code_server is None:
            return JsonResponse({'code':400, 'errmsg':'图形验证码失效'})
        # 如果提取出验证码， 提前删除，避免在有效期内测试验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 对比验证码, redis 中的数据是bytes字节, 需要转码
        image_code_server = image_code_server.decode()
        # 转为小写比较
        if image_code_server.lower() != image_code_client.lower():
            return JsonResponse({'code':400, 'errmsg':'输入图形有误'})
        # 如果验证码有效， 生成短信验证码
        sms_code = '%06d' % random.randint(0,999999)

        p1 = redis_conn.pipeline()
        p1.setex('sms_%s' % mobile,300, sms_code)

        # 设置频繁发送短信flag， 发送短信验证码
        p1.setex('send_flag_%s' % mobile, 60, 1)
        p1.execute()
        CCP().send_template_sms(mobile,[sms_code, 5], 1)

        # 返回相应结果
        return JsonResponse({'code':0, 'errmsg':'发送短信成功'})



import json
import os

from alipay import AliPay
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from orders.models import OrderInfo
from payment.models import Payment


class PaymentView(View):
    def get(self, request, order_id):
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'order_id错误'})
        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 调用对象的方法
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )
        # 拼接url
        url = settings.ALIPAY_URL + '?' + order_string
        return JsonResponse({'code':0, 'errmsg':'ok', 'alipay_url':url})


class PaymentStatusView(View):
    def put(self, request):
        dict = request.GET.dict()
        signature = dict.pop('sign')
        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        isSuccess = alipay.verify(dict, signature)
        if isSuccess:
            order_id = dict.get('out_trade_no')
            trade_id = dict.get('trade_no')
            try:
                Payment.objects.create(
                    order_id=order_id,
                    trade_id=trade_id
                )
                OrderInfo.objects.filter(order_id=order_id, status=1).update(stauts=4)
            except Exception as e:
                return JsonResponse({'code':400, 'errmsg':'保存失败'})
            return JsonResponse({'code':400, 'errmsg':'ok', 'trade_id':trade_id})

        else:
            return JsonResponse({'code':400, 'errmsg':'非法请求'})


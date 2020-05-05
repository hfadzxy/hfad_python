import base64
import pickle

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
import json
# Create your views here.
from django_redis import get_redis_connection

from goods.models import SKU


class CartsView(View):
    def post(self, request):
        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 判断参数
        if not all([sku_id, count]):
            return JsonResponse({'code':400, 'errmsg':'参数缺少'})
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'sku不存在'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'count错误'})
        # 判断selected 是否为bool
        if selected:
            if not isinstance(selected , bool):
                return JsonResponse({'code':400, 'errmsg':'selected错误'})
        # 判断是否登录
        if request.user.is_authenticated:
            # 操作购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hincrby('carts_%s' % request.user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % request.user.id, sku_id)
            pl.execute()
            return JsonResponse({'code':0, 'errmsg':'添加购物车成功'})
        else:
            # 操作cookie
            cookie_cart = request.COOKIES.get('carts')
            # 如果操作过cookie购物车
            if cookie_cart:
                # 将cookie_cart 解码为base64的bytes 再转为字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}
            # 判断加入购物车的sku_id 是否已在购物车中
            if sku_id in cart_dict:
                count += cart_dict[sku_id]['count']
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            # 将字典转为bytes 再转为base64的bytes
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({'code':0, 'errmsg':'添加购物车成功'})
            response.set_cookie('carts', cart_data)
            return response


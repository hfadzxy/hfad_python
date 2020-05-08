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

    def get(self, request):
        # 1. 判断是否登录，
        if request.user.is_authenticated:
            # 2. 如果登录， 获取链接对象
            redis_conn = get_redis_connection('carts')
            # 3. 在hash中获取对应的数据：dict
            item_dict = redis_conn.hgetall('carts_%s' % request.user.id)
            # 4. 在set中获取对应的数据： 集合
            selected_items = redis_conn.smembers('selected_%s' %request.user.id)
            cart_dict = {}
            # 5. 把hash中sku_id & count放入{}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)]={
                    'count':int(count),
                    # 6. 判断hash中的sku_id是否再set中
                    'selected':sku_id in selected_items
                }
        else:
        # 7. 如果用户未登录
            cookie_cart = request.COOKIES.get('carts')
        # 8. 从cookie中获取数据
        # 9. 判断数据存在， 如果存在， 解密为dict
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
        # 10. 如果不存在， 创建dict
            else:
                cart_dict = {}
        # 11 根据dict， 获取对应的key: sku_dis
        sku_ids = cart_dict.keys()
        # 12. 把sku_ids变为sku对象
        try:
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'错误'})
        list = []
        for sku in skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'price':sku.price,
                'count':cart_dict.get(sku.id).get('count'),
                'amount':(sku.price * cart_dict.get(sku.id).get('count')),
                'selected':cart_dict.get(sku.id).get('selected')
            })
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'cart_skus':list})

    def put(self, request):
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 判断参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '参数缺少'})
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': 'sku不存在'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': 'count错误'})
        # 判断selected 是否为bool
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': 'selected错误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 创建redis链接对象
            redis_conn = get_redis_connection('carts')
            # 创建管道
            pl = redis_conn.pipeline()
            # 修改购物侧
            pl.hset('carts_%s' %user.id, sku_id, count)
            # 判断selected, 病更改
            if selected:
                pl.sadd('selected_%s' %user.id, sku_id)
            else:
                pl.srem('selected_%s' %user.id, sku_id)
            # 提交管道
            pl.execute()
            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected
            }
            return JsonResponse({'code':0, 'errmsg':'ok', 'cart_sku':cart_sku})
        else:
            # 用户未登录， 读取cookie数据
            cookie_cart = request.COOKIE.get('carts')
            # 如果数据存在， 解密为字典
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            # 如果数据不存在， 创建空字典
            else:
                cart_dict = {}
            # 写入字典
            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected
            }
            # 将字典进行加密
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({'code':0, 'errmsg':'ok', 'cart_sku':cart_sku})
            response.set_cookie('carts', cart_data)
            return response

    def delete(self, request):
        # 接收参数
        dict = json.loads(request.body.decode())
        sku_id = dict.get('sku_id')
        selected = dict.get('selected')
        # 检验参数
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'错误id'})
        # 判断用户是否登录
        user = request.user
        if user is not None and user.is_authenticated:
            # 如果用户登录
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 删除sku_id
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            # 返回json
            return JsonResponse({'code':0, 'errmsg':'ok'})
        # 如果用户未登录
        else:
            # 从cookie中取值
            cookie_cart = request.COOKIE.get('carts')
            # 如果有值， 解密
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode))
            else:
                cart_dict = {}
            response = JsonResponse({'code':0, 'errmsg':'ok'})
            # 判断sku_id是否在dict中
            if sku_id in cart_dict:
                # 如果在删除sku_id
                del cart_dict[sku_id]
                # 加密dict
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 写入cookie
                response.set_cookie('carts', cart_data)
            # 返回json
            return response


class CartSelectAllView(View):
    def put(self, request):
        dict = json.loads(request.body.decode())
        selected = dict.get('selected')
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code':400,
                                     'errmsg':'selected参数有误'})
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            sku_ids = item_dict.keys()
            if selected:
                redis_conn.sadd('selected_%s' % user.id,  *sku_ids)
            else:
                redis_conn.srem('selected_%s' % user.id, *sku_ids)
            return JsonResponse({'code':0, 'errmsg':'ok'})
        else:
            cookie_cart = request.COOKIE.get('carts')
            response = JsonResponse({'code':0, 'errmsg':'ok'})
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
                for sku_id in cart_dict.keys():
                    cart_dict[sku_id]['selected'] = selected
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cart_data)
            return response



class CartsSimpleView(View):
    def get(self, request):
        # 1. 判断是否登录，
        if request.user.is_authenticated:
            # 2. 如果登录， 获取链接对象
            redis_conn = get_redis_connection('carts')
            # 3. 在hash中获取对应的数据：dict
            item_dict = redis_conn.hgetall('carts_%s' % request.user.id)
            # 4. 在set中获取对应的数据： 集合
            selected_items = redis_conn.smembers('selected_%s' %request.user.id)
            cart_dict = {}
            # 5. 把hash中sku_id & count放入{}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)]={
                    'count':int(count),
                    # 6. 判断hash中的sku_id是否再set中
                    'selected':sku_id in selected_items
                }
        else:
        # 7. 如果用户未登录
            cookie_cart = request.COOKIES.get('carts')
        # 8. 从cookie中获取数据
        # 9. 判断数据存在， 如果存在， 解密为dict
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
        # 10. 如果不存在， 创建dict
            else:
                cart_dict = {}
        # 11 根据dict， 获取对应的key: sku_dis
        sku_ids = cart_dict.keys()
        # 12. 把sku_ids变为sku对象
        try:
            skus = SKU.objects.filter(id__in=sku_ids)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'错误'})
        list = []
        for sku in skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'count':cart_dict.get(sku.id).get('count'),
            })
        print(list)
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'cart_skus':list})
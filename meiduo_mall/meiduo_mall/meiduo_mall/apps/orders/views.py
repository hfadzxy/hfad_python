import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import Address


class OrderSettlementView(View):
    def get(self, request):
        user = request.user
        try:
            addresses = Address.objects.filter(user=user,is_deleted=False)
        except Exception as e:
            addresses = None
        redis_conn = get_redis_connection('carts')
        item_dict = redis_conn.hgetall('carts_%s' %user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(item_dict[sku_id])
        sku_list = []
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'count':cart[sku.id],
                'price':sku.price
            })
        freight = Decimal('10.00')
        list = []
        for address in addresses:
            list.append({
                'id':address.id,
                'province':address.province.name,
                'city':address.city.name,
                'district':address.district.name,
                'place':address.place,
                'receiver':address.place,
                'mobile':address.mobile
            })
        context = {
            'addresses':list,
            'skus':sku_list,
            'freight':freight
        }

        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'context':context})


# class OrderCommitView(View):
#     def post(self, request):
#         '''保存订单信息和保存订单商品信息'''
#         json_dict = json.loads(request.body.decode())
#         address_id = json_dict.get('address_id')
#         pay_method = json_dict.get('pay_method')
#         if not all([address_id, pay_method]):
#             return JsonResponse({'code':400, 'errmsg':'缺少参数'})
#         try:
#             address = Address.objects.filter(id=address_id)
#         except Exception as e:
#             return JsonResponse({'code':400, 'errmsg':'address_id错误'})
#         if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
#             return JsonResponse({'code':400, 'errmsg':'pay_method错误'})
#         user = request.user
#         # 生成订单编号： 年月日时分秒+用户编号
#         order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
#         OrderInfo.objects.create(
#             order_id = order_id,
#             user = user,
#             address = address,
#             total_count = 0,
#             total_amount = Decimal('0'),
#             freight = Decimal('10.00'),
#             pay_method=pay_method,
#             status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']
#             if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
#             else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
#         )
#         order = OrderInfo.objects.get(id=order_id)
#
#         # 保存订单商品信息
#         redis_conn = get_redis_connection('carts')
#         item_dict = redis_conn.hgetall('carts_%s' % user.id)
#         cart_selected = redis_conn.smembers('selected_%s' % user.id)
#         carts = {}
#         for sku_id in cart_selected:
#             carts[int(sku_id)] = int(item_dict[sku_id])
#         sku_ids = carts.keys()
#         for sku in sku_ids:
#             sku = SKU.objects.get(id=sku_id)
#             sku_count = carts[sku.id]
#             # 判断库存是否满足
#             if sku_count > sku.stock:
#                 return JsonResponse({'code':400, 'errmsg':'库存不足'})
#             # sku=减少库存
#             sku.stock -= sku_count
#             sku.sales += sku_count
#             sku.save
#
#             # 修改SPU销量
#             sku.goods.sales += sku_count
#             sku.goods.save()
#
#             # 保存订单商品信息
#             OrderGoods.objects.create(
#                 order = order,
#                 sku=sku,
#                 count=sku_count,
#                 price=sku.price
#             )
#
#             order.total_count += sku_count
#             order.total_amount += (sku_count * sku.price)
#
#         order.total_amount += order.freight
#         order.save()
#
#         # 清楚购物侧中已结算的商品
#         redis_conn.hdel('carts_%s' % user.id, *cart_selected)
#         redis_conn.srem('selected_%s' % user.id, *cart_selected)
#
#         return JsonResponse({'code':0, 'errmsg':'下单成功', 'order_id':order.order_id})


class OrderCommitView(View):
    def post(self, request):
        # 1. 接受json参数
        dict = json.loads(request.body.decode())
        address_id = dict.get('address_id')
        pay_method = dict.get('pay_method')
        # 2. 总体检测
        if not all([address_id, pay_method]):
            return JsonResponse({'code':400, 'errmsg':'缺少参数'})
        # 4. 检测address
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'address_id有误'})
        if pay_method not in [1, 2]:
            return JsonResponse({'code':400, 'errmsg':'pay_method有误'})
        # 创建订单id
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % request.user.id)
        # 4. 订单信息表中保存数据
        # 开启事务
        with transaction.atomic():
            save_id = transaction.savepoint()
            order = OrderInfo.objects.create(
                order_id = order_id,
                user = request.user,
                address = address,
                total_count = 0,
                total_amount = Decimal('0.00'),
                freight = Decimal('10.00'),
                pay_method=pay_method,
                status=1 if pay_method==2 else 2
            )
            # 链接redis 获取链接对象
            redis_conn = get_redis_connection('carts')
            # hash中获取count值
            item_dict = redis_conn.hgetall('carts_%s' % request.user.id)
            # set中获取sku_ids
            selected_item = redis_conn.smembers('selected_%s'% request.user.id)
            dict = {}
            for sku_id in selected_item:
                dict[int(sku_id)] = int(item_dict[sku_id])
            # 遍历sku_ids 获取sku_id
            for sku_id in dict.keys():
                while True:
                    # 从SKU中获取sku对象
                    sku = SKU.objects.get(id=sku_id)
                    sales_count = dict.get(sku_id)
                    # 记录原始库存和销量
                    origin_stock = sku.stock
                    origin_sales = sku.sales
                    # 判断sku库存和销量关系
                    if sales_count > sku.stock:
                        # 库存不足， 数据库回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'code':400, 'errmsg':'库存不足'})
                        # 更改sku中stock 和 sales
                        #sku.stock -= sales_count
                        #sku.sales += sales_count
                        #sku.save()
                    new_stock = origin_stock - sales_count
                    new_sales = origin_sales + sales_count
                    result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,sales=new_sales)
                    if result == 0:
                        continue
                    # 更改sku对应类别sales,保存
                    sku.goods.sales += sales_count
                    sku.goods.save()
                    # 给订单商品表增加数据
                    OrderGoods.objects.create(
                        order = order,
                        sku=sku,
                        count=sales_count,
                        price=sku.price
                    )
                    # 更新OrderInfo 数据
                    order.total_count += sales_count
                    order.total_amount +=  (sku.price * sales_count)
                    break
                order.total_amount += order.freight
                order.save()
            transaction.savepoint_commit(save_id)
        # 删除redis中set表中对应的sku_id, hash删除
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' %request.user.id, *selected_item)
        pl.srem('selected_%s' % request.user.id, *selected_item)
        pl.execute()
        # 返回
        return JsonResponse({'code':0, 'errmsg':'ok', 'order_id':order.order_id})

from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from goods.models import SKU
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



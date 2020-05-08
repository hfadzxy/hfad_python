import base64
import pickle

from django_redis import get_redis_connection


def merge_carts_cookie_redis(request, response):
    '''合并cookie和redis中的购物车数据'''
    # 读取cookie数据
    cookie_cart = request.COOKIES.get('carts')
    # 判断数据是否存在 ， 如果村组，解密
    if not cookie_cart:
        return response
    cart_dict = pickle.loads(base64.b64decode(cookie_cart))
    # 把dict分为3个部分， dict， add ， remove
    new_dict = {}
    new_add = []
    new_remove = []
    for sku_id, dict in cart_dict.items():
        new_dict[sku_id] = dict['count']
        if dict['selected']:
            new_add.append(sku_id)
        else:
            new_remove.append(sku_id)
    # 链接redis，获取对象
    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()
    # 往hash中增加数据，
    user = request.user
    redis_conn.hmset('carts_%s' % user.id, new_dict)
    # 判断add是否有值， 有的话往set增加数
    if new_add:
        pl.sadd('selected_%s' % user.id, *new_add)
    if new_remove:
        pl.srem('selected_%s' % user.id, *new_remove)
    pl.execute()
    response.delete_cookie('carts')
    return response


from collections import OrderedDict

from goods.models import GoodsChannel, GoodsCategory


def get_breadcrumb(category):
    '''获取最低级别的类别， 获取各个类别的名称'''
    dict = {
        'cat1':'',
        'cat2':'',
        'cat3':''
     }
    if category.parent is None:
        dict['cat1'] = category.name
    elif category.parent.parent is None:
        dict['cat1'] = category.name
        dict['cat2'] = category.parent.name
    else:
        dict['cat3'] = category.name
        dict['cat2'] = category.parent.name
        dict['cat1'] = category.parent.parent.name

    return dict


def get_categories():
    # 第一部分: 从数据库中取数据:
    # 定义一个有序字典对象
    categories = OrderedDict()

    # 对 GoodsChannel 进行 group_id 和 sequence 排序, 获取排序后的结果:
    channels = GoodsChannel.objects.order_by('group_id',
                                             'sequence')

    # 遍历排序后的结果: 得到所有的一级菜单( 即,频道 )
    for channel in channels:
        # 从频道中得到当前的 组id
        group_id = channel.group_id

        # 判断: 如果当前 组id 不在我们的有序字典中:
        if group_id not in categories:
            # 我们就把 组id 添加到 有序字典中
            # 并且作为 key值, value值 是 {'channels': [], 'sub_cats': []}
            categories[group_id] = {
                'channels': [],
                'sub_cats': []
            }

        # 获取当前频道的分类名称
        cat1 = channel.category

        # 给刚刚创建的字典中, 追加具体信息:
        # 即, 给'channels' 后面的 [] 里面添加如下的信息:
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 根据 cat1 的外键反向, 获取下一级(二级菜单)的所有分类数据, 并遍历:
        cat2s = GoodsCategory.objects.filter(parent=cat1)
        # cat1.goodscategory_set.all()
        for cat2 in cat2s:
            # 创建一个新的列表:
            cat2.sub_cats = []
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            # 根据 cat2 的外键反向, 获取下一级(三级菜单)的所有分类数据, 并遍历:
            for cat3 in cat3s:
                # 拼接新的列表: key: 二级菜单名称, value: 三级菜单组成的列表
                cat2.sub_cats.append(cat3)
            # 所有内容在增加到 一级菜单生成的 有序字典中去:
            categories[group_id]['sub_cats'].append(cat2)

from django import http
from collections import OrderedDict
from goods.models import GoodsCategory
from goods.models import GoodsChannel, SKU
from goods.models import SKUImage, SKUSpecification
from goods.models import GoodsSpecification, SpecificationOption

def get_goods_and_spec(sku_id):

    # ======== 获取该商品和该商品对应的规格选项id ========
    try:
        # 根据 sku_id 获取该商品(sku)
        sku = SKU.objects.get(id=sku_id)
        # 获取该商品的图片
        sku.images = SKUImage.objects.filter(sku=sku)
    except Exception as e:
        return http.JsonResponse({'code': 400,
                                  'errmsg': '获取数据失败'})

    # 获取该商品的所有规格: [颜色, 内存大小, ...]
    sku_specs = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')

    sku_key = []
    # 获取该商品的所有规格后,遍历,拿取一个规格

    for spec in sku_specs:
        # 规格 ----> 规格选项 ----> 选项id  ---> 保存到[]
        sku_key.append(spec.option.id)

    # ======== 获取类别下所有商品对应的规格选项id ========
    # 根据sku对象,获取对应的类别
    goods = sku.goods

    # 获取该类别下面的所有商品
    skus = SKU.objects.filter(goods=goods)

    dict = {}
    for temp_sku in skus:
        # 获取每一个商品(temp_sku)的规格参数
        s_specs = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')

        key = []
        for spec in s_specs:
            # 规格 ---> 规格选项 ---> 规格选项id ----> 保存到[]
            key.append(spec.option.id)

        # 把 list 转为 () 拼接成 k : v 保存到dict中:
        dict[tuple(key)] = temp_sku.id

    # ======== 在每个选项上绑定对应的sku_id值 ========
    specs = GoodsSpecification.objects.filter(goods=goods).order_by('id')

    for index, spec in enumerate(specs):
        # 复制当前sku的规格键
        key = sku_key[:]
        # 该规格的选项
        spec_options = SpecificationOption.objects.filter(spec=spec)

        for option in spec_options:
            # 在规格参数sku字典中查找符合当前规格的sku
            key[index] = option.id
            option.sku_id = dict.get(tuple(key))

        spec.spec_options = spec_options

    return goods, specs, sku

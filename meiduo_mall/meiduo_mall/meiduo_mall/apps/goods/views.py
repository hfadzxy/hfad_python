from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

# Create your views here.
from goods.models import GoodsCategory, SKU
from goods.utils import get_breadcrumb


class ListView(View):
    def get(self, request, category_id):
        '''接受商品的三级id, 排序后返回'''
        # 1. 接受参数
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')
        # 2. 根据3级id， 获取对应类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'查询商品出错'})
        # 面包屑导航
        breadcrumb = get_breadcrumb(category)


        # 3. 根据该类别， 查询商品，排序
        try:
            skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'获取商品出错'})
        # 4. 根据分页类创建分页对象
        paginator = Paginator(skus, page_size)
        # 5. 调用page函数, 获取对应的商品
        try:
            page_skus = paginator.page(page)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'page出错'})
        # 6. 获取总页码
        total_pages = paginator.num_pages
        # 7. 遍历获取对应页码商品
        list = []
        for sku in page_skus:
            list.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image_url
            })

        # 8. 返回json
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'breadcrumb':breadcrumb,
            'list':list,
            'count':total_pages

        })



class HotGoodsView(View):
    def get(self, request, category_id):
        # 1. 获取是商品
        try:
            category = GoodsCategory.objects.get(id=category_id)
            skus = SKU.objects.filter(category=category, is_launched=True).order_by('-sales')[:2]
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'获取商品错误'})
        list = []
        for sku in skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'price':sku.price,
                'name':sku.name
            })
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'hot_skus':list
        })




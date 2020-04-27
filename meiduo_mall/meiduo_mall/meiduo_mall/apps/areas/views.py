from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
# Create your views here.
from areas.models import Area


class ProvinceAreasView(View):
    def get(self, request):
        # 查询省级数据
        list = cache.get('province')
        if not list:
            try:
                province_model_list = Area.objects.filter(parent__isnull=True)
                # 创建列表
                list = []
                # 获取对象中的信息，添加到空列表
                for province in province_model_list:
                    list.append({
                        'id':province.id,
                        'name':province.name
                    })
                cache.set('province', list, 3600)
            except Exception as e:
                return JsonResponse({'code':400, 'errmsg':'获取省份数据出错'})
        # 返回前端
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'province_list':list,
                             })

class SubAreaView(View):
    def get(self, request, pk):
        sub_data = cache.get('sub_data_'+pk)
        if not sub_data:
            try:
                # 查询所有市或区
                sub_model_list = Area.objects.filter(parent=pk)
                # 查询省份数据
                parent_model = Area.objects.get(id=pk)
                sub_list = []
                for sub_model in sub_model_list:
                    sub_list.append({'id':sub_model.id,
                                     'name':sub_model.name
                                     })
                sub_data = {
                    'id':parent_model.id,
                    'name':parent_model.name,
                    'subs':sub_list
                }
                cache.set('sub_data_'+pk, dict, 3600)
            except Exception as e:
                return JsonResponse({'code':400, 'errmsg':'查询数据错误'})
        return JsonResponse({'code':0,
                             'errmsg':'OK',
                             'sub_data':sub_data
                             })



from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from .models import *
from datetime import date

# Create your views here.

class SaveDataView(View):
    def get(self, request):
        book = BookInfo(
            btitle = '西游记',
            bpub_date = date(1990, 10, 10),
            bread = 100,
            bcomment = 1000,
            is_delete = False
        )
        book.save()
        return HttpResponse('OK')

    # BookInfo.objects.create(
    #     btitle='上品寒士',
    #     bpub_date = date(2000, 10, 10),
    #     bread = 100,
    #     bcomment = 1000,
    #     is_delete = False
    # )
#
    # 查询
def func(View):
    book = BookInfo.objects.get(id=1)
    print('get:',book)
    print('get:',book.btitle)
    book = BookInfo.objects.all()
    print('all:', book)
    num = BookInfo.objects.count()
    print('count:', num)

    # 过滤查询
    book = BookInfo.objects.filter(id=1)
    print('filter:',book)


    # 删除： delete()
    # book = BookInfo.objects.get(id=8)
    # book.delete()

    # book = BookInfo.objects.filter(id__in=[14,15])
    # book.delete()

    # BookInfo.objects.filter(id__gte=6).delete()

    # 修改 查询集.update（） update 前面要是一个集合 filter, all, exclude, order by
    # BookInfo.objects.exclude(id=1).update(bpub_date=date(2000, 10, 10))

    # book = BookInfo.objects.get(id=1)
    # book.字段 = ’xxx'
    # book.save()



    # 2个属性进行比较: F对象
    from django.db.models import F
    book = BookInfo.objects.filter(bread__gte=F('bcomment'))
    print('F:', book)

    # 逻辑运算 ： Q对象
    book = BookInfo.objects.filter(id__gt=3, bread__gt=50)
    print('Q:', book)
    from django.db.models import Q
    book = BookInfo.objects.filter(Q(bread__gt=20))
    print('Q:', book)

    # 非：～
    book = BookInfo.objects.filter(~Q(id=3))
    print('Q:~', book)


    # 聚合函数 aggregate()  Avg, Count, Max, Min, Sum,
    from django.db.models import Max
    sum_bread = BookInfo.objects.aggregate(Max('bread'))
    print(sum_bread)

    # 排序 order by
    book = BookInfo.objects.order_by('bread')
    print(book)
    book = BookInfo.objects.order_by('-bread')
    print(book)

    # 多对一查询
    book = HeroInfo.objects.get(id=1).hbook
    print('多对一：',book)

    # 一对多查询
    # 指向多的小名
    # book = BookInfo.objects.get(id=1).subs
    # print('一对多(外键小名related_name)：', book)

    # 指向 模型类名小写_set
    book = BookInfo.objects.get(id=1)
    print('_set:', book, type(book))
    book = book.heroinfo_set.all()
    print('一的对象.模型类名小写_set(heroinfo_set):', book)

    return HttpResponse('ok')
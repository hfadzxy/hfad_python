from django.template import loader
from django.conf import settings
import sys
sys.path.insert(0, '../')
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'
import django
django.setup()
from celery_tasks.html.tasks import generate_static_sku_detail_html
from goods.utils import get_categories
from goods.models import SKU


if __name__ == '__main__':
    # 获取所有的商品信息
    skus = SKU.objects.all()
    # 遍历拿出所有的商品:
    for sku in skus:
        print(sku.id)
        # 调用我们之前在 celery_tasks.html.tasks 中写的生成商品静态页面的方法:
        # 我们最好把这个函数单独复制过来, 这样可以不依靠 celery, 否则必须要开启celery
        generate_static_sku_detail_html(sku.id)
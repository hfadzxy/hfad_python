from django.db import models

# Create your models here.
from meiduo_mall.utils.Basemodel import BaseModel
from django.db import models


# 定义QQ登录的模型类
class QAuthQQUser(BaseModel):
    # 建立user外键
    user = models.ForeignKey('users.User',
                             on_delete=models.CASCADE,
                             verbose_name='用户')
    openid = models.CharField(max_length=64,
                              verbose_name='openid',
                              db_index=True)
    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name




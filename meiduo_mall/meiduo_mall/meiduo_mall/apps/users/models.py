from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    # 增加mobile字段
    mobile = models.CharField(max_length=11, unique=True, verbose_name='电话号码')

    # 增加一个字段， email_active 用于邮箱是否激活
    email_active = models.BooleanField(default=False, verbose_name='邮箱激活')

    class Meta:
        db_table = 'tb_users'
        # 指定当前表的中文
        verbose_name = '用户名'
        # 制定当前表复数
        verbose_name_plural = verbose_name

        def __str__(self):
            return self.username

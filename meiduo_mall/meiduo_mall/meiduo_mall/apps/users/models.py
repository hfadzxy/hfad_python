from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from itsdangerous import TimedJSONWebSignatureSerializer, BadData

from meiduo_mall.settings import dev


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


    def generate_access_token(self):
        obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=1800)
        dict = {
            'user_id':self.id,
            'email':self.email
        }
        token = obj.dumps(dict).decode()
        return dev.EMAIL_VERIFY_URL + token

    @staticmethod
    def check_verify_token(token):
        obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=1800)
        try:
            dict = obj.loads(token)
        except BadData:
            return None
        else:
            user_id = dict.get('user_id')
            email = dict.get('email')
        try:
            user = User.objects.get(id=user_id,email=email)
        except Exception as e:
            return None
        else:
            return user





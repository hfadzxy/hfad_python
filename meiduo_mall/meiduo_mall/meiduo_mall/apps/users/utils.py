from django.contrib.auth.backends import ModelBackend
import re

from meiduo_mall.settings import dev
from users.models import User
from itsdangerous import TimedJSONWebSignatureSerializer


def get_user_by_account(account):
    '''判断account是username还是mobile'''
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)

        else:
            user = User.objects.get(username=account)
    except Exception as e:
        return None
    else:
        return user


class UsernameMobileAuthentication(ModelBackend):
    '''重写认证函数： 使其具有手机认证功能'''
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 自定义一个函数， 用来区分username保存的类型： username/mobile
        user = get_user_by_account(username)
        if user and user.check_password(password):
            return user



def generate_access_token(user):
    obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=1800)
    dict = {
        'user_id':user.id,
        'email':user.email
    }
    token = obj.dumps(dict).decode()
    return dev.EMAIL_VERIFY_URL + obj


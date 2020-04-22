from django.test import TestCase
from itsdangerous import TimedJSONWebSignatureSerializer
# from django.conf import settings
from meiduo_mall.meiduo_mall.settings import dev


# Create your tests here.
if __name__ == "__main__":
    # obj = TimedJSONWebSignatureSerializer(秘钥, 有效期 )
    # data + 盐（秘钥） ========> itsdangerous =========>  加密的字符串
    obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=600)

    dict = {'name':'zs', 'age':12}
    # 加密方法dumps
    access_token = obj.dumps(dict)
    # 二进制转为str
    access_token = access_token.decode()
    print(access_token)

    data = obj.loads(access_token)
    print(data)
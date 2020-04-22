from itsdangerous import TimedJSONWebSignatureSerializer
from meiduo_mall.meiduo_mall.settings import dev


def generate_access_token_by_openid(openid):
    obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=600)
    dict = {'openid':openid}
    return obj.dumps(dict).decode()

from itsdangerous import TimedJSONWebSignatureSerializer
from meiduo_mall.settings import dev


def generate_access_token_by_openid(openid):
    '''把openid加密为token'''
    obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=600)
    dict = {'openid':openid}
    return obj.dumps(dict).decode()


def check_access_token(access_token):
    '''把access_token解密为openid'''
    obj = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=600)
    try:
        data = obj.loads(access_token)
    except Exception as e:
        return None
    else:
        return data['openid']




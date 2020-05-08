from django.contrib.auth import login, authenticate, logout

from carts.utils import merge_carts_cookie_redis
from celery_tasks.email.tasks import send_verify_email
from django.shortcuts import render
from django_redis import get_redis_connection
import re
import json
from django.views import View
import logging

from goods.models import SKU
from oauth.utils import check_access_token
from users.utils import generate_access_token
logger = logging.getLogger('django')
from meiduo_mall.utils.view import LoginRequireMixin
from users.models import User, Address
from django.http import JsonResponse, HttpResponse

# Create your views here.
class UsernameCountView(View):
    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
            print(count)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'访问数据库失败'})

        return JsonResponse({'code':0, 'errmsg':'ok', 'count':count})


class MobileCountView(View):
    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'访问数据库出错'})

        return JsonResponse({'code':0, 'errmsg':'ok', 'count':count})


class RegisterView(View):
    def post(self, request):
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')
        # 检测全部参数是否全
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return JsonResponse({'code':404, 'errmsg':'缺少必传参数'})

        # username 检测
        if not re.match(r'[a-zA-Z_-]{5,20}$', username):
            return JsonResponse({'code':404, 'errmsg':'username格式错误'})

        # password 检测
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return JsonResponse({'code':404, 'errmsg':'password格式错误'})
        if password2 != password:
            return JsonResponse({'code':404, 'errmsg':'两次输入不对'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return  JsonResponse({'code':400, 'errmsg':'mobile格式错误'})

        if allow != True:
            return JsonResponse({'code':400, 'errmsg':'allow格式错误'})

        # 检测sms_code
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'code':400, 'errmsg':'短信验证码过期'})
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code':400,'errmsg':'验证码有误'})
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'保存到数据库'})

        # 实现状态保持
        login(request, user)

        # 增加合并购物车
        response = JsonResponse({'code':0, 'errmsg':'ok'})
        response = merge_carts_cookie_redis(request, response)
        return response


class LoginView(View):
    def post(self, request):
        # 接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')
        # 检测参数是否全
        if not all([username, password]):
            return JsonResponse({'code':400, 'errmsg':'缺少参数'})

        # 验证是否登录,返回布尔
        user = authenticate(username=username, password=password)

        # 判断是否为空
        if user is None:
            return JsonResponse({'code':400, 'errmsg':'用户名或密码错误'})

        # 状态保持
        login(request, user)

        # 判断是否记住用户
        if remembered != True:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)


        # 返回cookie 用户名
        response = JsonResponse({'code':0, 'errmsg':'ok'})
        response.set_cookie('username', user.username, max_age=3600*24*14)
        response = merge_carts_cookie_redis(request, response)

        # 返回json
        return response


class LogoutView(View):
    def delete(self, request):
        # 删除session信息：logout()
        logout(request)
        response = JsonResponse({'code':0,'errmsg':'ok'})
        # 清理cookie
        response.delete_cookie('username')
        return response


class UserInfoView(LoginRequireMixin, View):
    def get(self, request):
        dict = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'info_data':dict
                             })


class EmailView(View):
    def put(self, request):
        '''保存email到数据库， 给邮箱发送邮件'''
        # 接受参数
        dict = json.loads(request.body.decode())
        email = dict.get('email')

        # 检验参数， 判断该参数是否有值
        if not email:
            return JsonResponse({'code':400, 'errmsg':'缺少必传参数'})

        # 检测email格式
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code':400, 'errmsg':'email格式不正确'})

        # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400, 'errmsg':'添加邮箱失败'})

        # 给注册有邮箱发送激活邮件
        # verify_url = generate_access_token(request.user)
        verify_url = request.user.generate_access_token()
        send_verify_email.delay(email, verify_url)

        return JsonResponse({'code':0, 'errmsg':'ok'})


class VerifyEmailView(View):
    def put(self, request):
        '''获取前端传入token解密， 获取user， 更改用户email_active'''
        token = request.GET.get('token')
        if not token:
            return JsonResponse({'code':400, 'errmsg':'token为空  '})
        user = User.check_verify_token(token)
        if not user:
            return JsonResponse({'code':400, 'errmsg':'token错误'})
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'保存数据库错误'})
        return JsonResponse({'code':0, 'errmsg':'ok'})


class CreateAddressView(View):
    def post(self, request):
        # 获取有效地址数量, is_deleted=False
        try:
            count = Address.objects.filter(user=request.user,
                                           is_deleted=False
                                           ).count()
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'获取地址数据错误'})
        # 判断地址数量
        if count >= 20:
            return JsonResponse({'code':400, 'errmsg':'超过地址数量上限'})
        # 满足条件接受参数
        dict = json.loads(request.body.decode())
        receiver = dict.get('receiver')
        province_id = dict.get('province_id')
        city_id = dict.get('city_id')
        district_id = dict.get('district_id')
        place = dict.get('place')
        mobile = dict.get('mobile')
        tel = dict.get('tel')
        email = dict.get('email')
        # 总体检测
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code':400, 'errmsg':'缺少参数'})
        # 检测mobile,tel, email
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code':400, 'errmsg':'mobile不符'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code':400, 'errmsg':'参数tel错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code':400, 'errmsg':'参数email错误'})
        # 添加地址
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400, 'errmsg':'添加地址错误'})
        # 返回地址, 注意字典， address.province.name
        address_dict = {
            'id':address.id,
            'title':address.title,
            'receiver':address.receiver,
            'province':address.province.name,
            'city':address.city.name,
            'district':address.district.name,
            'place':address.place,
            'mobile':address.mobile,
            'tel':address.tel,
            'email':address.email
        }
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'address':address_dict
                             })


class AddressView(View):
    def get(self, request):
        # 根据user获取有效地址集
        addresses = Address.objects.filter(user=request.user, is_deleted=False)
        # 建立返回的地址列表
        address_dict_list = []
        # 循环获取添加地址
        for address in addresses:
            address_dict ={
                'id':address.id,
                'title':address.title,
                'receiver':address.receiver,
                'province':address.province.name,
                'city':address.city.name,
                'district':address.district.name,
                'place':address.place,
                'mobile':address.mobile,
                'tel':address.tel,
                'email':address.email,
            }
            # 获取默认地址
            default_address = request.user.default_address
            # 判断默认地址，将其插入表头
            if default_address.id == address.id:
                address_dict_list.insert(0, address_dict)
            else:
                address_dict_list.append(address_dict)
        default_id = request.user.default_address_id
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'addresses':address_dict_list,
                             'default_address_id':default_id
                             })


class UpdatedestroyAddressView(View):
    # 接受修改后参数
    def put(self, request, address_id):
        dict = json.loads(request.body.decode())
        receiver = dict.get('receiver')
        province_id = dict.get('province_id')
        city_id = dict.get('city_id')
        district_id = dict.get('district_id')
        place = dict.get('place')
        mobile = dict.get('mobile')
        tel = dict.get('tel')
        email = dict.get('email')
        # 总体检测
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '缺少参数'})
        # 检测mobile,tel, email
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': 'mobile不符'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400, 'errmsg': '参数tel错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '参数email错误'})
        # 修改地址
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            address = Address.objects.get(id=address_id)
        # 数据库没有地址， 报错
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400, 'errmsg':'数据库地址修改错误'})
        # 构造响应报文
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email,
        }
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'address':address_dict
                             })

    def delete(self, request, address_id):
        try:
            # 获取对象
            address = Address.objects.get(id=address_id)
            # 逻辑删除
            address.is_deleted = True
            # 数据保存
            address.save()
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'删除失败'})

        return JsonResponse({'code':0, 'errmsg':'ok'})


class DefaultAddressView(View):
    def put(self, request, address_id):
        try:
            # 修改对象
            # address = Address.ojbects.get(id=address_id)
            # request.user.default_address = address
            # request.user.save()

            # 修改id
            request.user.default_address_id = address_id
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400, 'errmsg':'设置默认地址错误'})
        return JsonResponse({'code':0, 'errmsg':'设置默认地址成功'})


class UpdateTitleAddressView(View):
    def put(self, request, address_id):
        # 获取json字典
        dict = json.loads(request.body.decode())
        # 获取title
        title = dict.get('title')
        # 修改title:
        try:
            address = Address.objects.get(id=address_id)
            address.title = title
            address.save()
            # update
            # Address.objects.filter(id=address_id).update(title=title)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'修改失败 '})
        return JsonResponse({'code':0, 'errmsg':'ok'})


class ChangePasswordView(LoginRequireMixin, View):
    def put(self, request):
        dict = json.loads(request.body.decode())
        old_password = dict.get('old_password')
        new_password = dict.get('new_password')
        new_password2 = dict.get('new_password2')
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code':400, 'errmsg':'缺少参数'})
        result = request.user.check_password(old_password)
        if not result:
            return JsonResponse({'code':400, 'errmsg':'原密码错误'})
        if not re.match(r'', new_password):
            return JsonResponse({'code':400, 'errmsg':'新密码不规范'})
        if new_password != new_password2:
            return JsonResponse({'code':400, 'errmsg':'新密码不相等'})
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code':400, 'errmsg':'修改密码错误'})
        logout(request)
        response = JsonResponse({'code':0, 'errmsg':'密码修改成功'})
        response.delete_cookie('username')
        return response

class UserBrowseHistory(View):
    def post(self, request):
        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 判断sku_id
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code':400, 'errmsg':'sku_id错误'})
        # 创建redis链接对象
        redis_conn = get_redis_connection('history')
        # 建立管道
        pl = redis_conn.pipeline()
        user_id = request.user.id
        # 去重， pl.lrem
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 储存
        pl.lpush('history_%s' % user_id, sku_id)
        # 截取前 5 个
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()
        # 返回响应
        return JsonResponse({'code':400, 'errmsg':'ok'})

    def get(self, request):
        # 获取redis 中的sku_id 信息
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)
        # 根据sku_id 查询对应的信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'price':sku.price
            })
        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'skus':skus})






























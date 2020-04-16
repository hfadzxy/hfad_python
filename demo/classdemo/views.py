from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse

# Create your views here.

class Classview1(View):
    def get(self, request):
        print('Class1 get')
        return HttpResponse("Class1 get")

    def post(self, request):
        print('Class1 post')
        return HttpResponse('Class1 post')




def my_decorator(func):
    def inner(request, *args, **kwargs):
        print('装饰器调用')
        print('请求路径%s' % request.path)
        return func(request, *args, **kwargs)
    return inner

class Classview2(View):
    def get(self, request):
        print('class2 get')
        return HttpResponse('class2 get')

    def post(self, request):
        print('class2 post')
        return HttpResponse('class2 post')


from django.utils.decorators import method_decorator
class Classview3(View):
    @method_decorator(my_decorator)
    def get(self, request):
        print('class3 get')
        return HttpResponse('class3 get')
    @method_decorator(my_decorator)
    def post(self, request):
        print('class3 post')
        return HttpResponse('class3 post')


# @method_decorator(my_decorator, name='get')
@method_decorator(my_decorator, name='dispatch')
class Classview4(View):
    def get(self, request):
        print('class4 get')
        return HttpResponse('class4 get')

    def post(self, request):
        print('class4 post')
        return HttpResponse('class4 post')

from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.views.generic.base import View

# Create your views here.

def my_decorator_1(func):
    def inner(request, *args, **kwargs):
        print('装饰器1调用')
        print('请求路径%s' % request.path)
        return func(request, *args, **kwargs)
    return inner

def my_decorator_2(func):
    def inner(request, *args, **kwargs):
        print('装饰器2调用')
        print('请求路径%s' % request.path)
        return func(request, *args, **kwargs)
    return inner


class Firstmixin(object):
    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        view = my_decorator_1(view)
        return view

class Secondmixin(object):
    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super().as_view(*args, **kwargs)
        view = my_decorator_2(view)
        return view


class Mixin1(Firstmixin, Secondmixin, View):
    def get(self, request):
        print('demoview get')
        return HttpResponse('demoview get')

    def post(self, request):
        print('demoview post')
        return HttpResponse('demoview post')









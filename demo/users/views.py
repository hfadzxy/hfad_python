from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
# Create your views here.


def index(request):
    # request.session['name'] = 'lisi'
    # value = request.session.get('name')
    # print(value)
    print('index')
    return HttpResponse('index')


def say(requst):
    print('say')
    return HttpResponse('say')


def sayhello(request):
    print('sayhello')
    result = reverse('us:say')
    return HttpResponse(result)



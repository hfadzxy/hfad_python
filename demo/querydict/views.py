from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.


def getquerydict(request):
    print('querydict')
    a = request.GET.get('a')
    print(a)
    b = request.GET.get('b')
    print(b)
    a = request.GET.getlist('a')
    print(a)
    return HttpResponse('GET')


def postquerydict(request):
    a = request.POST.get('a')
    print(a)
    b = request.POST.get('b')
    print(b)
    a = request.POST.getlist('a')
    print(a)
    return HttpResponse('POST')

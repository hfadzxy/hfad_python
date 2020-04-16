from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def message(request, name, age):
    print('urlrequest')
    print(name, age)
    return HttpResponse('urlrequest')

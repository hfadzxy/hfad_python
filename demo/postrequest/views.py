from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.


def postmessage(request):
    result = request.POST.get('a')
    print(result)
    result = request.POST.getlist('a')
    print(result)
    return HttpResponse('postrequest')
    

from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
import json
from django.urls import reverse

from django.http import JsonResponse


# Create your views here.


def nonformmessage(request):
    #bity = request.body
    #string = bity.decode('utf-8')
    #result = json.loads(string)
    result = request.META['CONTENT_TYPE']
    print(result)
    result = request.META['CONTENT_LENGTH']
    print(result)
    result = json.loads(request.body.decode())
    print(result)

    method = request.method
    user = request.user
    path = request.path
    code = request.encoding
    print(method, user, path, code)

    num = '{"name":"zs"}'
    # return HttpResponse(num, content_type="application/json", status=404)
    response = HttpResponse('itcast', status=404)
    response['itcast'] = 'python'
    # return response

    num = {'name':'zs', 'age':20}
    # return JsonResponse(num)
    url = reverse('us:index')
    # return redirect(url)

    response = HttpResponse()
    response.set_cookie('itcast', 'python', max_age = 3600)
    value = request.COOKIES.get('itcast')
    print(value)
    return response
def my_middleware_1(get_response):
    print('init被调用了')
    def middleware(request_a):
        print('before request 被调用了')
        response = get_response(request_a)
        print('after response被调用了')
        return response
    return middleware

def my_middleware_2(get_response):
    print('init2被调用了')
    def middleware(request):
        print('before request 被调用')
        response = get_response(request)
        print('after response被调用')
        return response
    return middleware



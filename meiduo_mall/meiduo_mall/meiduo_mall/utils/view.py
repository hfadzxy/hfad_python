from django import http


def my_decorator(view):
    def wrapper(request, *args, **kwargs):
        if request.usr.is_authenticated:
            return view(request, *args, **kwargs)
        else:
            return http.JsonResponse({'code':400, 'errmsg':'请登录后重试'})
    return wrapper


class LoginRequireMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return my_decorator(view)

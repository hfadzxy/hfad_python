def get_breadcrumb(category):
    '''获取最低级别的类别， 获取各个类别的名称'''
    dict = {
        'cat1':'',
        'cat2':'',
        'cat3':''
     }
    if category.parent is None:
        dict['cat1'] = category.name
    elif category.parent.parent is None:
        dict['cat1'] = category.name
        dict['cat2'] = category.parent.name
    else:
        dict['cat3'] = category.name
        dict['cat2'] = category.parent.name
        dict['cat1'] = category.parent.parent.name

    return dict
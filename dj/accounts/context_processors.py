def current_page(request):
    if request.GET:
        path = u'%s?%s' % (request.path, request.GET.urlencode())
    else:
        path = request.path
    return {'current_page': path}

from django.http import JsonResponse

def api_response(status='success', message='', data=None, http_code=200, api_code=''):
    return JsonResponse({
        'status': status,
        'message': message,
        'api_code': api_code,
        'data': data or {}
    }, status=http_code)

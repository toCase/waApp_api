from django.http import HttpResponse

class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем origin из заголовков
        origin = request.META.get('HTTP_ORIGIN')
        
        # Список разрешенных origins
        allowed_origins = [
            'https://tocase.github.io',
            'https://t78481548vc14789.pp.ua',
            'http://localhost:30000',
            'http://127.0.0.1:30000',
        ]
        
        # Обработка preflight запросов
        if request.method == "OPTIONS":
            response = HttpResponse()
            if origin in allowed_origins or not origin:  # Разрешаем если origin в списке или отсутствует
                response["Access-Control-Allow-Origin"] = origin or "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-CSRFToken"
            response["Access-Control-Max-Age"] = "86400"
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        response = self.get_response(request)
        
        # Добавляем CORS заголовки к ответу
        if origin in allowed_origins or not origin:
            response["Access-Control-Allow-Origin"] = origin or "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-CSRFToken"
        response["Access-Control-Allow-Credentials"] = "true"
        
        return response
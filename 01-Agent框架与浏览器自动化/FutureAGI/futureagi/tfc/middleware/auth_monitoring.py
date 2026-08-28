import structlog
from django.core.cache import cache

logger = structlog.get_logger(__name__)


class AuthMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Monitor failed auth attempts
        if hasattr(request, "user") and not request.user.is_authenticated:
            client_ip = self.get_client_ip(request)
            failed_attempts = cache.get(f"failed_auth_{client_ip}", 0)

            if failed_attempts > 5:  # Rate limiting
                # logger.warning(f"Multiple failed auth attempts from IP: {client_ip}")
                #     return JsonResponse({'error': 'Too many failed attempts'}, status=429)
                pass

            cache.set(f"failed_auth_{client_ip}", failed_attempts + 1, 300)  # 5 minutes

        response = self.get_response(request)

        if response.status_code in [401, 403]:
            logger.warning(
                f"Auth failure: {request.path} - "
                f"User: {getattr(request.user, 'username', 'anonymous')} - "
                f"IP: {self.get_client_ip(request)}"
            )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        return (
            x_forwarded_for.split(",")[0]
            if x_forwarded_for
            else request.META.get("REMOTE_ADDR")
        )

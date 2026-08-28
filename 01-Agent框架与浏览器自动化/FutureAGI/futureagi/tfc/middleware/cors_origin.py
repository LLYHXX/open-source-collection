class OriginCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        import re

        from tfc.settings import settings

        # Compile regex patterns once at initialization
        self.allowed_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        self.regex_patterns = []
        for pattern in getattr(settings, "CORS_ORIGIN_REGEX_WHITELIST", []):
            self.regex_patterns.append(re.compile(pattern))

    def __call__(self, request):
        origin = request.headers.get("Origin")

        # Only check if Origin header is present
        if origin:
            # Check against allowed origins
            if origin not in self.allowed_origins:
                # Check against regex patterns
                for pattern in self.regex_patterns:
                    if pattern.match(origin):
                        break

                # if not matches:
                #     from django.http import HttpResponseForbidden

                #     return HttpResponseForbidden("Invalid origin")

        return self.get_response(request)

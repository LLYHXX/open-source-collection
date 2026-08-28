import time
import traceback

import structlog

logger = structlog.get_logger(__name__)


class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Log incoming request
        # logger.info(f"[DEBUG] Request received: {request.method} {request.path}")
        # logger.info(f"[DEBUG] Request headers: {dict(request.headers)}")

        response = self.get_response(request)

        # Log response time
        time.time() - start_time
        # logger.info(f"[DEBUG] Response time: {request.path} took {process_time:.2f} seconds {response.status_code}")

        return response

    def process_exception(self, request, exception):
        logger.error(f"[DEBUG] Exception in request: {str(exception)}")
        logger.error(f"[DEBUG] Full traceback: {''.join(traceback.format_exc())}")
        return None

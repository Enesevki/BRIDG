# gamehost_project/middleware.py

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from games.utils import get_client_ip

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Custom middleware to add additional security headers and CORS monitoring.
    """
    
    def process_response(self, request, response):
        """
        Add security headers to all responses.
        """
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # API-specific headers
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Log CORS requests for monitoring
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            client_ip = get_client_ip(request)
            logger.info(
                f"CORS request from origin: {origin}, IP: {client_ip}, "
                f"Path: {request.path}, Method: {request.method}"
            )
        
        return response


class CORSSecurityMiddleware(MiddlewareMixin):
    """
    Additional CORS security checks and rate limiting.
    """
    
    # Suspicious patterns to monitor
    SUSPICIOUS_ORIGINS = [
        'null',
        'data:',
        'file:',
        'chrome-extension:',
        'moz-extension:',
    ]
    
    def process_request(self, request):
        """
        Perform additional CORS security checks.
        """
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # Block suspicious origins
        if any(suspicious in origin.lower() for suspicious in self.SUSPICIOUS_ORIGINS):
            client_ip = get_client_ip(request)
            logger.warning(
                f"Blocked suspicious origin: {origin} from IP: {client_ip}"
            )
            return JsonResponse(
                {
                    'error': 'Forbidden origin',
                    'code': 'invalid_origin'
                }, 
                status=403
            )
        
        # Monitor unusual request patterns
        if origin and request.path.startswith('/api/'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Log potential bot activity
            if not user_agent or len(user_agent) < 10:
                logger.warning(
                    f"Suspicious request - minimal user agent: '{user_agent}' "
                    f"from origin: {origin}, IP: {get_client_ip(request)}"
                )
        
        return None


class APIVersionMiddleware(MiddlewareMixin):
    """
    Add API version information to responses.
    """
    
    def process_response(self, request, response):
        """
        Add API version header to API responses.
        """
        if request.path.startswith('/api/'):
            response['X-API-Version'] = '1.0'
            response['X-GameHost-Version'] = '2025.1'
        
        return response 
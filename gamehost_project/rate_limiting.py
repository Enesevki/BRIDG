# gamehost_project/rate_limiting.py
"""
Simple Rate Limiting System for GameHost Platform
- Uses Django cache backend only
- No external dependencies
- Clean middleware + decorator approach
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


# =============================================================================
# Rate Limiting Utilities
# =============================================================================

def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_cache_key(key_type, identifier, endpoint=None):
    """Create consistent cache keys for rate limiting."""
    if endpoint:
        return f"rate_limit:{key_type}:{identifier}:{endpoint}"
    return f"rate_limit:{key_type}:{identifier}"


def is_rate_limited(cache_key, requests_per_hour):
    """Check if a cache key is rate limited."""
    current_time = int(time.time())
    window_start = current_time - 3600  # 1 hour window
    
    # Get current request count for this hour
    request_count = cache.get(cache_key, 0)
    
    if request_count >= requests_per_hour:
        return True, request_count
    
    # Increment request count
    new_count = request_count + 1
    cache.set(cache_key, new_count, timeout=3600)  # 1 hour
    
    return False, new_count


def add_rate_limit_headers(response, cache_key, requests_per_hour):
    """Add rate limiting headers to response."""
    request_count = cache.get(cache_key, 0)
    remaining = max(0, requests_per_hour - request_count)
    
    response['X-RateLimit-Limit'] = str(requests_per_hour)
    response['X-RateLimit-Remaining'] = str(remaining)
    response['X-RateLimit-Reset'] = str(int(time.time()) + 3600)
    
    return response


# =============================================================================
# Simple Rate Limiting Middleware
# =============================================================================

class SimpleRateLimitMiddleware(MiddlewareMixin):
    """
    Simple global rate limiting middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        logger.info("SimpleRateLimitMiddleware initialized")
    
    def process_request(self, request):
        """Process incoming requests for rate limiting."""
        try:
            logger.debug(f"Rate limit middleware processing: {request.path}")
            
            # Skip rate limiting for certain paths
            if self._should_skip_rate_limiting(request):
                logger.debug(f"Skipping rate limiting for: {request.path}")
                return None
            
            # Get client IP
            client_ip = get_client_ip(request)
            
            # Check if user is authenticated (this happens after AuthenticationMiddleware)
            # For now, we'll treat all requests as anonymous since middleware order matters
            is_authenticated = False
            user_id = None
            
            # Check if user attribute exists (after AuthenticationMiddleware)
            if hasattr(request, 'user') and request.user.is_authenticated:
                is_authenticated = True
                user_id = request.user.id
                
                # Skip for superuser
                if request.user.is_superuser:
                    logger.debug(f"Skipping rate limiting for superuser: {request.user.username}")
                    return None
            
            # Determine rate limit key and limit
            if is_authenticated:
                cache_key = create_cache_key('user', user_id, request.path)
                requests_per_hour = 1000  # Higher limit for authenticated users
            else:
                cache_key = create_cache_key('ip', client_ip, request.path)
                requests_per_hour = 100  # Lower limit for anonymous users
            
            # Check rate limit
            is_limited, current_count = is_rate_limited(cache_key, requests_per_hour)
            
            if is_limited:
                logger.warning(f"Rate limit exceeded for {cache_key}: {current_count}/{requests_per_hour}")
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'detail': f'Too many requests. Limit: {requests_per_hour}/hour',
                    'retry_after': 3600
                }, status=429)
            
            logger.debug(f"Rate limit OK for {cache_key}: {current_count}/{requests_per_hour}")
            return None
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {str(e)}")
            # Don't block requests if middleware fails
            return None
    
    def process_response(self, request, response):
        """Add rate limiting headers to response."""
        try:
            if self._should_skip_rate_limiting(request):
                return response
            
            client_ip = get_client_ip(request)
            
            # Check if user is authenticated
            is_authenticated = hasattr(request, 'user') and request.user.is_authenticated
            
            if is_authenticated:
                cache_key = create_cache_key('user', request.user.id, request.path)
                requests_per_hour = 1000
            else:
                cache_key = create_cache_key('ip', client_ip, request.path)
                requests_per_hour = 100
            
            # Add headers
            response = add_rate_limit_headers(response, cache_key, requests_per_hour)
            
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {str(e)}")
        
        return response
    
    def _should_skip_rate_limiting(self, request):
        """Determine if rate limiting should be skipped for this request."""
        # Skip for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico'
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return True
        
        # Skip for CORS preflight requests
        if request.method == 'OPTIONS':
            return True
        
        # Skip for superuser (safely check if user exists)
        try:
            if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
                return True
        except AttributeError:
            # User not available yet (before AuthenticationMiddleware)
            pass
        
        return False


# =============================================================================
# Rate Limiting Decorator
# =============================================================================

def rate_limit(requests_per_hour=100, key_type='ip'):
    """
    Simple rate limiting decorator for views.
    
    Args:
        requests_per_hour: Number of requests allowed per hour
        key_type: 'ip', 'user', or custom key
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self_or_request, *args, **kwargs):
            try:
                # Handle both DRF ViewSets (self, request) and function views (request)
                if hasattr(self_or_request, 'request'):
                    # DRF ViewSet case
                    request = self_or_request.request
                    view_instance = self_or_request
                    result = view_func(self_or_request, *args, **kwargs)
                else:
                    # Function-based view case
                    request = self_or_request
                    view_instance = None
                    result = view_func(self_or_request, *args, **kwargs)
                
                # Get identifier based on key type
                if key_type == 'user':
                    if not hasattr(request, 'user') or not request.user.is_authenticated:
                        identifier = get_client_ip(request)
                        cache_key_type = 'ip'
                    else:
                        identifier = request.user.id
                        cache_key_type = 'user'
                        
                        # Skip for superuser
                        if request.user.is_superuser:
                            return result
                else:
                    identifier = get_client_ip(request)
                    cache_key_type = 'ip'
                
                # Create cache key
                endpoint = f"{request.resolver_match.url_name}" if request.resolver_match else request.path
                cache_key = create_cache_key(cache_key_type, identifier, endpoint)
                
                # Check rate limit
                is_limited, current_count = is_rate_limited(cache_key, requests_per_hour)
                
                if is_limited:
                    logger.warning(f"Rate limit exceeded for decorator {cache_key}: {current_count}/{requests_per_hour}")
                    response = JsonResponse({
                        'error': 'Rate limit exceeded',
                        'detail': f'Too many requests for this action. Limit: {requests_per_hour}/hour',
                        'retry_after': 3600
                    }, status=429)
                else:
                    response = result
                
                # Add rate limit headers if response supports it
                if hasattr(response, '__setitem__'):  # Check if response supports header setting
                    response = add_rate_limit_headers(response, cache_key, requests_per_hour)
                
                return response
                
            except Exception as e:
                logger.error(f"Rate limiting decorator error: {str(e)}")
                # Don't block the view if rate limiting fails
                return view_func(self_or_request, *args, **kwargs)
        
        return wrapped_view
    return decorator


# Aliases for backward compatibility
api_rate_limit = rate_limit


# =============================================================================
# DRF Throttling Classes (Stub for compatibility)
# =============================================================================

class GameUploadThrottle:
    pass

class RatingThrottle:
    pass
    
class ReportThrottle:
    pass

class GameSearchThrottle:
    pass 
# gamehost_project/rate_limiting.py

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from functools import wraps
import logging
import time
from games.utils import get_client_ip

logger = logging.getLogger(__name__)


# =============================================================================
# DRF Throttling Classes
# =============================================================================

class GameUploadThrottle(UserRateThrottle):
    """Rate limiting for game uploads - more restrictive"""
    scope = 'game_upload'
    rate = '5/hour'  # Max 5 games per hour per user

class GameSearchThrottle(AnonRateThrottle):
    """Rate limiting for search queries"""
    scope = 'search'
    rate = '100/hour'  # Max 100 searches per hour per IP

class AuthenticatedUserThrottle(UserRateThrottle):
    """General rate limiting for authenticated users"""
    scope = 'user'
    rate = '1000/hour'  # Max 1000 requests per hour per user

class AnonUserThrottle(AnonRateThrottle):
    """Rate limiting for anonymous users"""
    scope = 'anon'
    rate = '200/hour'  # Max 200 requests per hour per IP

class LoginThrottle(AnonRateThrottle):
    """Strict rate limiting for login attempts"""
    scope = 'login'
    rate = '10/hour'  # Max 10 login attempts per hour per IP

class RatingThrottle(UserRateThrottle):
    """Rate limiting for game rating/voting"""
    scope = 'rating'
    rate = '100/hour'  # Max 100 ratings per hour per user

class ReportThrottle(UserRateThrottle):
    """Rate limiting for reporting games"""
    scope = 'report'
    rate = '20/hour'  # Max 20 reports per hour per user


# =============================================================================
# Custom Rate Limiting Decorators
# =============================================================================

def api_rate_limit(group='general', rate='100/h', methods=['GET', 'POST'], key=None):
    """
    Enhanced rate limiting decorator with better error handling.
    
    Args:
        group: Rate limit group name
        rate: Rate limit (e.g., '100/h', '10/m')
        methods: HTTP methods to apply rate limiting
        key: Custom key function for rate limiting
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Apply rate limiting
            @ratelimit(
                group=group,
                rate=rate,
                methods=methods,
                key=key or 'ip'
            )
            def rate_limited_view(request, *args, **kwargs):
                return view_func(request, *args, **kwargs)
            
            try:
                return rate_limited_view(request, *args, **kwargs)
            except Ratelimited:
                # Log rate limit violation
                client_ip = get_client_ip(request)
                user_info = f"User {request.user.id}" if request.user.is_authenticated else "Anonymous"
                
                logger.warning(
                    f"Rate limit exceeded for {user_info} from IP {client_ip} "
                    f"on {request.method} {request.path} (group: {group}, rate: {rate})"
                )
                
                # Return structured error response
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'detail': f'Too many requests. Rate limit: {rate}',
                    'code': 'rate_limit_exceeded',
                    'retry_after': get_retry_after(group, request),
                    'timestamp': time.time()
                }, status=429)
        
        return wrapped_view
    return decorator


def get_retry_after(group, request):
    """
    Calculate retry-after time in seconds based on rate limit group.
    """
    rate_configs = {
        'login': 3600,  # 1 hour
        'upload': 3600,  # 1 hour
        'rating': 1800,  # 30 minutes
        'search': 1800,  # 30 minutes
        'general': 900,  # 15 minutes
    }
    return rate_configs.get(group, 900)


# =============================================================================
# Rate Limiting Middleware
# =============================================================================

class GlobalRateLimitMiddleware(MiddlewareMixin):
    """
    Global rate limiting middleware for additional protection.
    """
    
    # Rate limits per endpoint pattern
    ENDPOINT_LIMITS = {
        '/api/auth/login/': {'rate': '20/h', 'key': 'ip'},
        '/api/games/games/': {'rate': '500/h', 'key': 'ip'},
        '/api/games/games/.*/(rate|report)/': {'rate': '50/h', 'key': 'user_or_ip'},
        '/api/users/': {'rate': '100/h', 'key': 'ip'},
    }
    
    def process_request(self, request):
        """
        Apply global rate limiting based on request patterns.
        """
        import re
        
        # Skip rate limiting for certain conditions
        if self._should_skip_rate_limiting(request):
            return None
        
        # Check rate limits for matching endpoints
        for pattern, config in self.ENDPOINT_LIMITS.items():
            if re.match(pattern, request.path):
                rate_key = self._get_rate_key(request, config['key'])
                cache_key = f"rate_limit:{pattern}:{rate_key}"
                
                if self._is_rate_limited(cache_key, config['rate']):
                    logger.warning(
                        f"Global rate limit exceeded for {rate_key} "
                        f"on {request.method} {request.path}"
                    )
                    
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'detail': 'Too many requests to this endpoint',
                        'code': 'global_rate_limit',
                        'endpoint': request.path,
                        'timestamp': time.time()
                    }, status=429)
        
        return None
    
    def _should_skip_rate_limiting(self, request):
        """
        Determine if rate limiting should be skipped for this request.
        """
        # Skip for superusers (check if user is available and authenticated)
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            return True
        
        # Skip for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        # Skip for health checks
        if request.path in ['/health/', '/status/', '/ping/']:
            return True
        
        return False
    
    def _get_rate_key(self, request, key_type):
        """
        Generate rate limiting key based on type.
        """
        if key_type == 'user_or_ip':
            if hasattr(request, 'user') and request.user.is_authenticated:
                return f"user:{request.user.id}"
            else:
                return f"ip:{get_client_ip(request)}"
        elif key_type == 'user':
            if hasattr(request, 'user') and request.user.is_authenticated:
                return f"user:{request.user.id}"
            else:
                return None
        else:  # ip
            return f"ip:{get_client_ip(request)}"
    
    def _is_rate_limited(self, cache_key, rate):
        """
        Check if rate limit is exceeded using cache.
        """
        # Parse rate (e.g., "20/h" -> 20 requests per hour)
        count, period = rate.split('/')
        count = int(count)
        
        period_seconds = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }.get(period, 3600)
        
        # Get current count from cache
        current_count = cache.get(cache_key, 0)
        
        if current_count >= count:
            return True
        
        # Increment counter
        try:
            cache.set(cache_key, current_count + 1, period_seconds)
        except Exception as e:
            logger.error(f"Cache error in rate limiting: {e}")
            # Don't block if cache fails
            return False
        
        return False


# =============================================================================
# Rate Limiting Utilities
# =============================================================================

class RateLimitMonitor:
    """
    Utility class for monitoring and analyzing rate limit patterns.
    """
    
    @staticmethod
    def log_rate_limit_event(request, group, rate, exceeded=False):
        """
        Log rate limiting events for analysis.
        """
        client_ip = get_client_ip(request)
        user_info = f"User {request.user.id}" if request.user.is_authenticated else "Anonymous"
        
        event_data = {
            'user': user_info,
            'ip': client_ip,
            'path': request.path,
            'method': request.method,
            'group': group,
            'rate': rate,
            'exceeded': exceeded,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'timestamp': time.time()
        }
        
        if exceeded:
            logger.warning(f"Rate limit exceeded: {event_data}")
        else:
            logger.info(f"Rate limit check: {event_data}")
    
    @staticmethod
    def get_rate_limit_status(request, group='general'):
        """
        Get current rate limit status for a request.
        """
        client_ip = get_client_ip(request)
        cache_key = f"rate_limit:{group}:{client_ip}"
        
        current_count = cache.get(cache_key, 0)
        
        return {
            'group': group,
            'current_count': current_count,
            'ip': client_ip,
            'cache_key': cache_key
        }


def get_rate_limit_headers(request, group, rate):
    """
    Generate rate limit headers for API responses.
    """
    try:
        # Parse rate
        count, period = rate.split('/')
        count = int(count)
        
        # Get current usage
        client_ip = get_client_ip(request)
        cache_key = f"rate_limit:{group}:{client_ip}"
        current_count = cache.get(cache_key, 0)
        
        remaining = max(0, count - current_count)
        
        # Calculate reset time
        period_seconds = {
            's': 1, 'm': 60, 'h': 3600, 'd': 86400
        }.get(period, 3600)
        
        reset_time = int(time.time()) + period_seconds
        
        return {
            'X-RateLimit-Limit': str(count),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time),
            'X-RateLimit-Group': group
        }
    
    except Exception as e:
        logger.error(f"Error generating rate limit headers: {e}")
        return {} 
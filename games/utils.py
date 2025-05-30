# backend/games/utils.py

import logging
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for better error responses.
    Provides consistent error format across the API.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get the view and request from context
        view = context.get('view', None)
        request = context.get('request', None)
        
        # Log the error
        if response.status_code >= 500:
            logger.error(
                f"Server error in {view.__class__.__name__ if view else 'Unknown'}: {str(exc)}",
                exc_info=True,
                extra={
                    'view': view.__class__.__name__ if view else None,
                    'method': request.method if request else None,
                    'path': request.path if request else None,
                    'user': request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else None
                }
            )
        
        # Customize error response format
        custom_response_data = {
            'error': True,
            'status_code': response.status_code,
            'message': 'An error occurred',
            'details': response.data,
            'timestamp': None
        }
        
        # Add timestamp
        from datetime import datetime
        custom_response_data['timestamp'] = datetime.now().isoformat()
        
        # Customize message based on status code
        if response.status_code == 400:
            custom_response_data['message'] = 'Bad Request - Invalid input data'
        elif response.status_code == 401:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == 403:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == 404:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == 405:
            custom_response_data['message'] = 'Method not allowed'
        elif response.status_code == 429:
            custom_response_data['message'] = 'Rate limit exceeded'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Internal server error'
            # Don't expose internal error details in production
            if not hasattr(request, 'user') or not request.user.is_staff:
                custom_response_data['details'] = 'An internal error occurred. Please try again later.'
        
        response.data = custom_response_data
    
    return response


def validate_filter_params(request, allowed_params=None):
    """
    Validate filter parameters to prevent invalid queries.
    
    Args:
        request: Django request object
        allowed_params: List of allowed parameter names
    
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    if allowed_params is None:
        allowed_params = [
            'genre', 'genre_slug', 'tag', 'tag_slug', 
            'search', 'creator', 'creator_username',
            'moderation_status', 'is_published',
            'created_after', 'created_before', 'ordering',
            'page', 'page_size'
        ]
    
    errors = []
    query_params = request.query_params
    
    # Check for unknown parameters
    unknown_params = set(query_params.keys()) - set(allowed_params)
    if unknown_params:
        errors.append(f"Unknown parameters: {', '.join(unknown_params)}")
    
    # Validate specific parameter formats
    for param, value in query_params.items():
        if param in ['genre', 'tag', 'creator']:
            # These should be integers
            if isinstance(value, list):
                for v in value:
                    if not v.isdigit():
                        errors.append(f"Parameter '{param}' must contain only integer values")
                        break
            elif not value.isdigit():
                errors.append(f"Parameter '{param}' must be an integer")
        
        elif param == 'is_published':
            # Should be boolean
            if value.lower() not in ['true', 'false', '1', '0']:
                errors.append(f"Parameter '{param}' must be a boolean (true/false)")
        
        elif param in ['created_after', 'created_before']:
            # Should be valid date format
            from django.utils.dateparse import parse_datetime, parse_date
            if not (parse_datetime(value) or parse_date(value)):
                errors.append(f"Parameter '{param}' must be a valid date/datetime format")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


class FilterValidationMixin:
    """
    Mixin to add filter validation to ViewSets.
    """
    
    def list(self, request, *args, **kwargs):
        # Validate filter parameters before processing
        validation_result = validate_filter_params(request)
        
        if not validation_result['valid']:
            return Response(
                {
                    'error': 'Invalid filter parameters',
                    'details': validation_result['errors'],
                    'code': 'invalid_filters'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().list(request, *args, **kwargs)


def safe_int_conversion(value, default=None):
    """
    Safely convert a value to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        int or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
    
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip 
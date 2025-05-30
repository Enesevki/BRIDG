# games/input_validation.py

import re
import html
import unicodedata
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Input Validation & Sanitization Configuration
# =============================================================================

# Dangerous patterns for XSS prevention
XSS_PATTERNS = [
    # Script tags
    r'<script[^>]*>.*?</script>',
    r'<script[^>]*>',
    r'</script>',
    
    # Event handlers
    r'on\w+\s*=',
    r'javascript:',
    r'vbscript:',
    r'data:text/html',
    
    # Meta and link redirects
    r'<meta[^>]*http-equiv[^>]*refresh',
    r'<link[^>]*href[^>]*javascript:',
    
    # Iframe and object embeds
    r'<iframe[^>]*src[^>]*javascript:',
    r'<object[^>]*data[^>]*javascript:',
    
    # Style injections
    r'<style[^>]*>.*?expression\s*\(',
    r'style\s*=.*?expression\s*\(',
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(?:;|\s)+(?:drop|delete|truncate|alter|create|insert|update|exec|execute|sp_|xp_)\s+",
    r"union\s+(?:all\s+)?select",
    r"(?:\/\*|\*\/|--|#)",
    r"(?:char|nchar|varchar|nvarchar)\s*\(\s*\d+\s*\)",
    r"(?:waitfor|delay)\s+time",
    r"(?:benchmark|sleep)\s*\(",
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r'\.\.[\\/]',
    r'[\\\/]\.\.[\\/]',
    r'\.\.%2f',
    r'\.\.%5c',
    r'%2e%2e%2f',
    r'%2e%2e%5c',
]

# Command injection patterns
COMMAND_INJECTION_PATTERNS = [
    r'[;&|`$]',
    r'(\|\||\&\&)',
    r'[\r\n]',
    r'[<>]',
]

# Profanity/inappropriate content patterns (basic)
INAPPROPRIATE_CONTENT_PATTERNS = [
    # Add your own profanity filter patterns
    r'\b(spam|scam|virus|malware|hack|crack|pirate)\b',
    r'(?:https?://)?(?:bit\.ly|tinyurl|t\.co)/\w+',  # Suspicious short URLs
]

# =============================================================================
# Input Validation Classes
# =============================================================================

class InputSecurityError(ValidationError):
    """Custom exception for input security violations"""
    pass


class TextValidator:
    """Validates and sanitizes text inputs"""
    
    @staticmethod
    def validate_game_title(title: str) -> str:
        """Validate and sanitize game title"""
        if not title or not title.strip():
            raise InputSecurityError("Game title cannot be empty.")
        
        # Basic length check
        title = title.strip()
        if len(title) < 3:
            raise InputSecurityError("Game title must be at least 3 characters long.")
        if len(title) > 100:
            raise InputSecurityError("Game title cannot exceed 100 characters.")
        
        # Sanitize HTML and dangerous characters
        title = TextValidator._sanitize_html_content(title)
        
        # Check for inappropriate content
        TextValidator._check_inappropriate_content(title, "game title")
        
        # Check for XSS attempts
        TextValidator._check_xss_attempts(title, "game title")
        
        return title
    
    @staticmethod
    def validate_game_description(description: str) -> str:
        """Validate and sanitize game description"""
        if not description or not description.strip():
            raise InputSecurityError("Game description cannot be empty.")
        
        # Basic length check
        description = description.strip()
        if len(description) < 10:
            raise InputSecurityError("Game description must be at least 10 characters long.")
        if len(description) > 2000:
            raise InputSecurityError("Game description cannot exceed 2000 characters.")
        
        # Sanitize HTML (allow basic formatting)
        description = TextValidator._sanitize_html_content(description, allow_basic_html=True)
        
        # Check for inappropriate content
        TextValidator._check_inappropriate_content(description, "game description")
        
        # Check for XSS attempts
        TextValidator._check_xss_attempts(description, "game description")
        
        # Check for SQL injection attempts
        TextValidator._check_sql_injection(description, "game description")
        
        return description
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate and sanitize username"""
        if not username or not username.strip():
            raise InputSecurityError("Username cannot be empty.")
        
        username = username.strip()
        
        # Length check
        if len(username) < 3:
            raise InputSecurityError("Username must be at least 3 characters long.")
        if len(username) > 30:
            raise InputSecurityError("Username cannot exceed 30 characters.")
        
        # Pattern check (alphanumeric + underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise InputSecurityError("Username can only contain letters, numbers, and underscores.")
        
        # Check for inappropriate content
        TextValidator._check_inappropriate_content(username, "username")
        
        return username
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize file names"""
        if not filename or not filename.strip():
            raise InputSecurityError("Filename cannot be empty.")
        
        filename = filename.strip()
        
        # Length check
        if len(filename) > 255:
            raise InputSecurityError("Filename cannot exceed 255 characters.")
        
        # Check for path traversal
        TextValidator._check_path_traversal(filename, "filename")
        
        # Sanitize dangerous characters
        filename = re.sub(r'[<>:"|?*\\]', '_', filename)
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        return filename
    
    @staticmethod
    def _sanitize_html_content(content: str, allow_basic_html: bool = False) -> str:
        """Sanitize HTML content"""
        if not allow_basic_html:
            # Strip all HTML tags
            content = strip_tags(content)
        else:
            # Allow only basic formatting tags
            allowed_tags = ['b', 'i', 'u', 'br', 'p', 'strong', 'em']
            # Simple tag filtering (in production, use a proper HTML sanitizer like bleach)
            for tag in allowed_tags:
                content = re.sub(f'<{tag}>', f'&lt;{tag}&gt;', content, flags=re.IGNORECASE)
                content = re.sub(f'</{tag}>', f'&lt;/{tag}&gt;', content, flags=re.IGNORECASE)
            
            # Strip all other tags
            content = strip_tags(content)
            
            # Restore allowed tags
            for tag in allowed_tags:
                content = content.replace(f'&lt;{tag}&gt;', f'<{tag}>')
                content = content.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
        
        # HTML escape dangerous characters
        content = html.escape(content, quote=False)
        
        # Normalize unicode
        content = unicodedata.normalize('NFKC', content)
        
        return content
    
    @staticmethod
    def _check_xss_attempts(content: str, field_name: str) -> None:
        """Check for XSS attempts"""
        content_lower = content.lower()
        
        for pattern in XSS_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"XSS attempt detected in {field_name}: {pattern}")
                raise InputSecurityError(f"Potentially dangerous content detected in {field_name}.")
    
    @staticmethod
    def _check_sql_injection(content: str, field_name: str) -> None:
        """Check for SQL injection attempts"""
        content_lower = content.lower()
        
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected in {field_name}: {pattern}")
                raise InputSecurityError(f"Potentially dangerous content detected in {field_name}.")
    
    @staticmethod
    def _check_path_traversal(content: str, field_name: str) -> None:
        """Check for path traversal attempts"""
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Path traversal attempt detected in {field_name}: {pattern}")
                raise InputSecurityError(f"Invalid path characters detected in {field_name}.")
    
    @staticmethod
    def _check_command_injection(content: str, field_name: str) -> None:
        """Check for command injection attempts"""
        for pattern in COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, content):
                logger.warning(f"Command injection attempt detected in {field_name}: {pattern}")
                raise InputSecurityError(f"Invalid characters detected in {field_name}.")
    
    @staticmethod
    def _check_inappropriate_content(content: str, field_name: str) -> None:
        """Check for inappropriate content"""
        content_lower = content.lower()
        
        for pattern in INAPPROPRIATE_CONTENT_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                logger.warning(f"Inappropriate content detected in {field_name}: {pattern}")
                raise InputSecurityError(f"Inappropriate content detected in {field_name}.")


class DataValidator:
    """Validates data types and structures"""
    
    @staticmethod
    def validate_id_list(id_list: Union[List[int], str], field_name: str, max_count: int = 10) -> List[int]:
        """Validate list of IDs (for genres, tags, etc.)"""
        if isinstance(id_list, str):
            try:
                # Try to parse as JSON-like string
                id_list = id_list.strip('[]').split(',')
                id_list = [int(x.strip()) for x in id_list if x.strip()]
            except (ValueError, AttributeError):
                raise InputSecurityError(f"Invalid {field_name} format. Must be a list of integers.")
        
        if not isinstance(id_list, list):
            raise InputSecurityError(f"{field_name} must be a list.")
        
        if len(id_list) == 0:
            raise InputSecurityError(f"At least one {field_name} must be selected.")
        
        if len(id_list) > max_count:
            raise InputSecurityError(f"Too many {field_name} selected. Maximum {max_count} allowed.")
        
        # Validate each ID
        validated_ids = []
        for item in id_list:
            try:
                id_int = int(item)
                if id_int <= 0:
                    raise InputSecurityError(f"Invalid {field_name} ID: {id_int}. Must be positive.")
                validated_ids.append(id_int)
            except (ValueError, TypeError):
                raise InputSecurityError(f"Invalid {field_name} ID: {item}. Must be an integer.")
        
        return validated_ids
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email"""
        if not email or not email.strip():
            raise InputSecurityError("Email cannot be empty.")
        
        email = email.strip().lower()
        
        # Basic email format validation (Django will do more detailed validation)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise InputSecurityError("Invalid email format.")
        
        # Check for suspicious patterns
        if re.search(r'[<>"\';\\]', email):
            raise InputSecurityError("Email contains invalid characters.")
        
        return email
    
    @staticmethod
    def validate_url(url: str, field_name: str = "URL") -> str:
        """Validate and sanitize URLs"""
        if not url or not url.strip():
            return ""
        
        url = url.strip()
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                raise InputSecurityError(f"{field_name} must use HTTP or HTTPS protocol.")
            
            # Check for suspicious domains
            suspicious_domains = ['bit.ly', 'tinyurl.com', 't.co']
            if any(domain in parsed.netloc.lower() for domain in suspicious_domains):
                logger.warning(f"Suspicious URL detected: {url}")
                raise InputSecurityError(f"{field_name} contains a suspicious domain.")
            
            # Check for XSS in URL
            TextValidator._check_xss_attempts(url, field_name)
            
        except Exception as e:
            if isinstance(e, InputSecurityError):
                raise
            raise InputSecurityError(f"Invalid {field_name} format.")
        
        return url


class FormValidator:
    """Validates complete forms and their interactions"""
    
    @staticmethod
    def validate_game_form(data: Dict[str, Any], is_partial: bool = False) -> Dict[str, Any]:
        """Validate complete game form data
        
        Args:
            data: Form data to validate
            is_partial: If True, don't require all fields (for PATCH updates)
        """
        validated_data = {}
        
        # Required fields (only for full form validation)
        if not is_partial:
            if 'title' not in data:
                raise InputSecurityError("Game title is required.")
            if 'description' not in data:
                raise InputSecurityError("Game description is required.")
        
        # Validate fields that are present
        if 'title' in data:
            validated_data['title'] = TextValidator.validate_game_title(data['title'])
        
        if 'description' in data:
            validated_data['description'] = TextValidator.validate_game_description(data['description'])
        
        # Optional fields
        if 'genre_ids' in data:
            validated_data['genre_ids'] = DataValidator.validate_id_list(
                data['genre_ids'], 'genre', max_count=5
            )
        
        if 'tag_ids' in data:
            validated_data['tag_ids'] = DataValidator.validate_id_list(
                data['tag_ids'], 'tag', max_count=10
            )
        
        # Pass-through file fields and other fields that don't need text validation
        file_fields = ['webgl_build_zip', 'thumbnail']
        boolean_fields = ['is_published']
        
        for field in file_fields + boolean_fields:
            if field in data:
                validated_data[field] = data[field]
        
        # Cross-field validation (only if we have both title and description)
        if 'title' in validated_data and 'description' in validated_data:
            FormValidator._validate_content_consistency(validated_data)
        
        return validated_data
    
    @staticmethod
    def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user registration form"""
        validated_data = {}
        
        # Required fields
        required_fields = ['username', 'email', 'password', 'password2']
        for field in required_fields:
            if field not in data:
                raise InputSecurityError(f"{field} is required.")
        
        # Validate fields
        validated_data['username'] = TextValidator.validate_username(data['username'])
        validated_data['email'] = DataValidator.validate_email(data['email'])
        
        # Password validation (basic - Django will do more)
        password = data['password']
        password2 = data['password2']
        
        if len(password) < 8:
            raise InputSecurityError("Password must be at least 8 characters long.")
        
        if password != password2:
            raise InputSecurityError("Passwords do not match.")
        
        validated_data['password'] = password
        validated_data['password2'] = password2
        
        return validated_data
    
    @staticmethod
    def _validate_content_consistency(data: Dict[str, Any]) -> None:
        """Validate consistency between different fields"""
        title = data.get('title', '')
        description = data.get('description', '')
        
        # Check if title and description are too similar (potential spam)
        if title and description:
            title_words = set(title.lower().split())
            desc_words = set(description.lower().split())
            
            if len(title_words) > 0:
                overlap = len(title_words.intersection(desc_words)) / len(title_words)
                if overlap > 0.8:  # 80% overlap
                    raise InputSecurityError(
                        "Title and description are too similar. Please provide more detailed description."
                    )


# =============================================================================
# Utility Functions
# =============================================================================

def sanitize_input(data: Any, validator_type: str = 'text') -> Any:
    """General input sanitization function"""
    if data is None:
        return None
    
    if isinstance(data, str):
        if validator_type == 'title':
            return TextValidator.validate_game_title(data)
        elif validator_type == 'description':
            return TextValidator.validate_game_description(data)
        elif validator_type == 'username':
            return TextValidator.validate_username(data)
        elif validator_type == 'filename':
            return TextValidator.validate_filename(data)
        elif validator_type == 'email':
            return DataValidator.validate_email(data)
        elif validator_type == 'url':
            return DataValidator.validate_url(data)
        else:
            return TextValidator._sanitize_html_content(data)
    
    elif isinstance(data, list):
        return [sanitize_input(item, validator_type) for item in data]
    
    elif isinstance(data, dict):
        return {key: sanitize_input(value, validator_type) for key, value in data.items()}
    
    return data


def validate_request_data(data: Dict[str, Any], form_type: str, is_partial: bool = False) -> Dict[str, Any]:
    """Validate complete request data based on form type
    
    Args:
        data: Request data to validate
        form_type: Type of form being validated
        is_partial: If True, allow partial validation (for PATCH updates)
    """
    if form_type == 'game':
        return FormValidator.validate_game_form(data, is_partial=is_partial)
    elif form_type == 'user_registration':
        return FormValidator.validate_user_registration(data)
    else:
        raise InputSecurityError(f"Unknown form type: {form_type}") 
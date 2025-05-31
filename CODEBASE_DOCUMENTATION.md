# Game Hosting Platform - Backend Codebase Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture) 
3. [Security Features](#security-features)
4. [API Endpoints](#api-endpoints)
5. [Models & Database](#models--database)
6. [Authentication & Authorization](#authentication--authorization)
7. [Rate Limiting](#rate-limiting)
8. [Input Validation](#input-validation)
9. [Configuration](#configuration)
10. [Custom Middleware](#custom-middleware)
11. [Environment Setup](#environment-setup)
12. [Error Handling](#error-handling)
13. [Django Signals](#django-signals)
14. [Testing](#testing)
15. [Deployment Guide](#deployment-guide)
16. [Performance & Optimization](#performance--optimization)
17. [Development Guide](#development-guide)

## 🎯 Project Overview

**Game Hosting Platform Backend** - Django REST Framework tabanlı oyun hosting sistemi.

### 🌟 Core Features
- ✅ **WebGL Oyun Hosting** - Oyun dosyaları yükleme ve hosting
- ✅ **Kullanıcı Yönetimi** - JWT tabanlı authentication + logout + password change
- ✅ **Oyun Rating Sistemi** - Like/Dislike ve değerlendirme
- ✅ **Content Moderation** - Admin onay sistemi
- ✅ **File Security** - Kapsamlı dosya güvenlik kontrolleri
- ✅ **Rate Limiting** - IP ve kullanıcı tabanlı hız sınırlaması
- ✅ **Input Validation** - XSS, SQL injection, path traversal koruması
- ✅ **Game Analytics** - Oynanma ve görüntülenme istatistikleri
- ✅ **Search & Filtering** - Genre, tag, search filtreleri
- ✅ **Custom Middleware** - Güvenlik, versioning, CORS kontrolleri
- ✅ **Comprehensive Logging** - Tüm uygulamalar için detaylı log sistemi
- ✅ **Signal System** - Otomatik rating count güncellemeleri

### 🏗️ Tech Stack
- **Backend Framework**: Django 5.2 + Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **File Storage**: Django File Storage
- **Caching**: Database Cache (rate limiting)
- **Security**: Custom input validation + file security system
- **Environment**: python-dotenv for configuration

---

## 🏛️ Architecture

### 📁 Project Structure
```
gamehost_platform/backend/
├── gamehost_project/          # Main project settings
│   ├── settings.py           # Django configuration
│   ├── urls.py              # Main URL routing
│   ├── rate_limiting.py     # Rate limiting system
│   ├── middleware.py        # Custom middleware classes
│   ├── wsgi.py             # WSGI application
│   └── asgi.py             # ASGI application
├── games/                   # Games app (core functionality)
│   ├── models.py           # Game, Rating, Report models
│   ├── views.py            # API ViewSets
│   ├── serializers.py      # DRF serializers  
│   ├── security.py         # File security validation
│   ├── input_validation.py # Input sanitization
│   ├── utils.py            # Utility functions
│   ├── permissions.py      # Custom permissions
│   ├── filters.py          # Search & filtering
│   └── admin.py           # Django admin configuration
├── users/                  # User management app
│   ├── views.py           # User registration/auth
│   └── serializers.py     # User serializers
├── interactions/          # User interactions (ratings, reports)
│   ├── models.py         # Rating, Report models
│   ├── signals.py        # Django signals for auto-updates
│   └── admin.py         # Admin interface
├── tests/                # Comprehensive test suite
│   ├── jwt_test.py      # JWT authentication tests
│   ├── jwt_register_test.py  # Registration with JWT
│   ├── jwt_logout_test.py  # JWT logout and token blacklisting
│   ├── change_password_test.py     # Password change functionality
│   ├── simple_game_upload_test.py  # Game upload tests
│   ├── file_security_test.py       # Security tests
│   └── input_validation_test.py    # Input validation tests
├── media/                # Uploaded files storage
├── static/              # Static files
└── logs/               # Application logs
```

### 🔄 Data Flow
1. **File Upload** → Security Validation → ZIP Processing → File Storage
2. **Game Creation** → Input Validation → Moderation Queue → Admin Approval
3. **User Rating** → Authentication → Published Game Check → Rating Storage → Signal Updates
4. **Game Access** → View Count → Play Count → Analytics Update

---

## 🛡️ Security Features

### 🔒 File Security System (`games/security.py`)

#### Multi-Layer Validation
- File extension validation (only `.zip` allowed)
- MIME type verification  
- File size limits (max 100MB)
- ZIP structure validation (requires `index.html`, `Build/`, `TemplateData/`)
- Malicious file detection
- Path traversal prevention

### 🧼 Input Validation System (`games/input_validation.py`)

#### XSS Protection
- Script tag detection and removal
- Event handler blocking (`onclick`, `onload`, etc.)
- JavaScript URL blocking (`javascript:`)
- HTML entity encoding

#### SQL Injection Prevention  
- SQL keyword detection (`DROP`, `UNION`, `SELECT`)
- Comment injection blocking (`--`, `/*`, `*/`)
- Parameter validation and sanitization

#### Path Traversal Protection
- Directory traversal detection (`../`, `..\\`)
- URL-encoded traversal detection (`%2e%2e%2f`)
- Absolute path blocking

### 🚦 Rate Limiting System (`gamehost_project/rate_limiting.py`)

#### Global Middleware
- **Anonymous Users**: 100 requests/hour (IP-based)
- **Authenticated Users**: 1000 requests/hour (user-based)
- **Superuser Bypass**: No limits for superusers
- **Path Exclusions**: `/admin/`, `/static/`, `/media/`, OPTIONS requests

#### Endpoint-Specific Limits
- **Game Upload**: 5 uploads/hour per user
- **Registration**: 10 registrations/hour per IP
- **Rating**: 100 ratings/hour per user
- **Reporting**: 20 reports/hour per user
- **Play Count**: 300 increments/hour per IP

---

## 📡 API Endpoints

### 🎮 Games API (`/api/games/`)

#### Game Management
```
GET    /api/games/games/              # List games (published only)
POST   /api/games/games/              # Upload new game (auth required)
GET    /api/games/games/{id}/         # Game detail
PATCH  /api/games/games/{id}/         # Partial update game (owner only)
PUT    /api/games/games/{id}/         # Full update game (owner only)
DELETE /api/games/games/{id}/         # Delete game (owner only)
```

#### Game Interactions
```
POST   /api/games/games/{id}/rate/               # Rate game (1=like, -1=dislike)
DELETE /api/games/games/{id}/unrate/             # Remove rating
POST   /api/games/games/{id}/report/             # Report game
POST   /api/games/games/{id}/increment_play_count/ # Increment play count
```

#### User-Specific Endpoints
```
GET    /api/games/games/my-liked/               # User's liked games
GET    /api/games/analytics/my-games/           # User's uploaded games (all states)
```

#### Metadata
```
GET    /api/games/genres/                       # Available genres
GET    /api/games/tags/                         # Available tags
```

### 👤 Users API (`/api/auth/`)

#### Authentication
```
POST   /api/auth/register/                      # User registration + auto-login
POST   /api/auth/login/                         # JWT login
POST   /api/auth/logout/                        # JWT logout (blacklist refresh token)
POST   /api/auth/change-password/               # Change user password (auth required)
POST   /api/auth/token/refresh/                 # Refresh JWT token
POST   /api/auth/verify/                        # Verify JWT token
```

#### Legacy Profile (Backward Compatibility)
```
GET    /api/auth-legacy/profile/                # User profile (for tests)
```

### 🔍 Search & Filtering

#### Query Parameters
```
GET /api/games/games/?search=snake               # Text search in title/description
GET /api/games/games/?genre=5                   # Filter by genre ID
GET /api/games/games/?tags=1,2,3                # Filter by tag IDs
GET /api/games/games/?ordering=created_at       # Sort by field
GET /api/games/games/?page=2                    # Pagination
```

#### Advanced Filtering
- **Genre Filtering**: Single or multiple genres
- **Tag Filtering**: Inclusive tag matching
- **Text Search**: Title and description search
- **Ordering**: `created_at`, `-created_at`, `title`, `play_count`, `likes_count`
- **Pagination**: 20 items per page (configurable)

---

## 💾 Models & Database

### 🎯 Game Model (`games/models.py`)
- **UUID Primary Key**: Secure, non-sequential IDs
- **User Relationships**: Creator, ratings, reports
- **File Fields**: WebGL build ZIP, thumbnail, entry point path
- **Publishing System**: `is_published`, `moderation_status`
- **Many-to-Many**: Genres, tags
- **Analytics**: Play count, view count, likes/dislikes count
- **Timestamps**: Created, updated

### ⭐ Rating Model (`interactions/models.py`)
- **Unique Constraint**: One rating per user per game
- **Rating Types**: 1 (LIKE), -1 (DISLIKE)
- **Published Only**: Only published games can be rated
- **Signal Integration**: Auto-updates game rating counts

### 🚨 Report Model (`interactions/models.py`)
- **Unique Constraint**: One report per user per game
- **Status Tracking**: PENDING, REVIEWED, RESOLVED
- **Published Only**: Only published games can be reported

### 🏷️ Genre & Tag Models (`games/models.py`)
- **Slug Fields**: URL-friendly identifiers
- **Unique Names**: Prevent duplicates

---

## 🔐 Authentication & Authorization

### 🎫 JWT Configuration
```python
# JWT Token Settings (in Django settings)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),     # 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),        # 7 days
    'ROTATE_REFRESH_TOKENS': True,                      # Security feature
    'BLACKLIST_AFTER_ROTATION': True,                  # Prevent reuse
    'ALGORITHM': 'HS256',                               # Signing algorithm
    'SIGNING_KEY': SECRET_KEY,                          # Use Django secret
    'AUTH_HEADER_TYPES': ('Bearer',),                  # Header format
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# Required app for logout functionality
INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt.token_blacklist',  # JWT token blacklisting for logout
    # ...
]
```

### 🛂 Permission Classes

#### Custom Permission: `IsOwnerOrReadOnly`
```python
# Read permissions for published games or owners/staff
# Write permissions only for owners
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read: Published games or owner/staff
        if request.method in permissions.SAFE_METHODS:
            return obj.is_published or (
                request.user.is_authenticated and (
                    obj.creator == request.user or 
                    request.user.is_staff
                )
            )
        # Write: Only owner
        return (request.user.is_authenticated and 
                obj.creator == request.user)
```

### 👤 User Registration Flow
1. **Input Validation**: Username, email, password security
2. **Uniqueness Check**: Prevent duplicate accounts
3. **User Creation**: Django User object
4. **JWT Generation**: Immediate authentication (Access + Refresh tokens)
5. **Auto-Login**: Return tokens for frontend

### 🚪 JWT Logout System

#### Token Blacklisting Strategy
```python
# Logout endpoint implementation
@rate_limit(requests_per_hour=60, key_type='user')
def post(self, request):
    refresh_token = request.data.get('refresh_token')
    token = RefreshToken(refresh_token)
    token.blacklist()  # Add to blacklist database
```

#### Security Features
- **Refresh Token Blacklisting**: Invalid tokens stored in database
- **Access Token Preservation**: Remains valid until natural expiry (1 hour)
- **Duplicate Logout Prevention**: Already blacklisted tokens rejected
- **Rate Limiting**: 60 logout attempts per hour per user
- **Authentication Required**: Must provide valid access token

#### Logout Flow
1. **Client Request**: Send refresh token + access token
2. **Token Validation**: Verify refresh token format and authenticity
3. **Blacklist Addition**: Add refresh token to blacklist table
4. **Immediate Effect**: Token refresh attempts fail instantly
5. **Client Cleanup**: Frontend clears stored tokens

#### Expected Response
```json
{
    "message": "Başarıyla çıkış yapıldı.",
    "detail": "Token geçersiz kılındı."
}
```

### 🔑 Password Change System

#### Secure Password Change Strategy
```python
# Password change endpoint implementation
@rate_limit(requests_per_hour=10, key_type='user')
def post(self, request):
    # 1. Validate old password
    if not user.check_password(old_password):
        raise ValidationError("Mevcut şifre yanlış.")
    
    # 2. Validate new password
    validate_password(new_password, user)
    
    # 3. Change password
    user.set_password(new_password)
    user.save()
    
    # 4. Generate new JWT tokens (security)
    refresh = RefreshToken.for_user(user)
    return new_tokens
```

#### Security Features
- **Old Password Verification**: Must provide current password
- **New Password Validation**: Django's built-in password validators
- **Password Uniqueness**: New password cannot be same as current
- **Strength Requirements**: Minimum 8 characters, complexity rules
- **Rate Limiting**: 10 password changes per hour per user
- **JWT Token Refresh**: New tokens generated after password change

#### Password Change Flow
1. **Authentication Required**: Must provide valid access token
2. **Old Password Check**: Verify current password for security
3. **New Password Validation**: Strength and uniqueness checks
4. **Password Update**: Secure password hashing and storage
5. **Token Regeneration**: Fresh JWT tokens for enhanced security
6. **Logging**: Security event logging for audit trail

#### Expected Request
```json
{
    "old_password": "CurrentPassword123!",
    "new_password": "NewSecurePassword456!",
    "new_password2": "NewSecurePassword456!"
}
```

#### Expected Response
```json
{
    "message": "Şifre başarıyla değiştirildi.",
    "detail": "Güvenlik için yeni token'lar oluşturuldu.",
    "tokens": {
        "refresh": "new_refresh_token...",
        "access": "new_access_token..."
    }
}
```

---

## ⚡ Rate Limiting

### 🌐 Global Middleware (`SimpleRateLimitMiddleware`)
- **IP-based limiting** for anonymous users (100/hour)
- **User-based limiting** for authenticated users (1000/hour)
- **Cache backend**: Database cache with 2-hour timeout
- **Headers added**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

### 🎯 Decorator-Based Limiting (`@rate_limit`)
```python
@rate_limit(requests_per_hour=5, key_type='user')      # Game upload
@rate_limit(requests_per_hour=10, key_type='ip')       # Registration
@rate_limit(requests_per_hour=100, key_type='user')    # Rating
@rate_limit(requests_per_hour=300, key_type='ip')      # Play count
```

---

## 🧹 Input Validation

### 🛡️ Validation Classes

#### TextValidator
- **Game titles**: Length, XSS, SQL injection protection
- **Descriptions**: Content filtering, size limits
- **Usernames**: Character restrictions, profanity filtering

#### DataValidator  
- **Email validation**: Format, domain checking
- **ID lists**: Type validation, existence checks
- **URLs**: Protocol validation, domain restrictions

#### FormValidator
- **Complete forms**: Cross-field validation
- **Partial updates**: PATCH support with `is_partial` parameter
- **Business logic**: Duplicate checks, ownership validation

### 🔄 Partial Update Support
- **PATCH requests**: Only validate provided fields
- **Required field bypass**: Don't require all fields for partial updates
- **Cross-field validation**: Still applied when relevant fields present

---

## ⚙️ Configuration

### 🔧 Django Settings (`gamehost_project/settings.py`)

#### Security
```python
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True  # False in production
ALLOWED_HOSTS = []  # Configure for production
```

#### Database Configuration
```python
# PostgreSQL (Production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

#### File Uploads Security
```python
FILE_UPLOAD_SECURITY = {
    'MAX_FILE_SIZE_MB': 50,
    'MAX_FILES_IN_ZIP': 1000,
    'ALLOWED_EXTENSIONS': ['.zip'],
    'ALLOWED_MIME_TYPES': ['application/zip'],
    'ENABLE_MAGIC_BYTE_CHECK': True,
    'ENABLE_CONTENT_SCANNING': True,
    'HIGH_ENTROPY_THRESHOLD': 7.5,
    'MAX_COMPRESSION_RATIO': 100,
}
```

#### CORS Configuration
```python
# Development CORS (Relaxed)
if DEBUG_CORS:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",     # React
        "http://localhost:5173",     # Vite
        "http://localhost:8080",     # Vue.js
    ]

# Production CORS (Strict)
else:
    CORS_ALLOWED_ORIGINS = [
        "https://yourdomain.com",
        "https://app.yourdomain.com",
    ]
```

### 📦 Dependencies
```python
# Core Dependencies
Django==5.2
djangorestframework==3.16.0
djangorestframework-simplejwt==5.3.1

# Database & Storage
psycopg2-binary==2.9.10
pillow==11.2.1

# CORS & Filtering
django-cors-headers==4.4.0
django-filter==24.3

# Configuration & Rate Limiting
python-dotenv==1.1.0
django-ratelimit==4.1.0
```

---

## 🔧 Custom Middleware

### 🛡️ SecurityHeadersMiddleware
- **Additional Security Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **API Cache Control**: no-cache, no-store for API endpoints
- **CORS Monitoring**: Logs cross-origin requests

```python
# Security headers added
response['X-Content-Type-Options'] = 'nosniff'
response['X-Frame-Options'] = 'DENY'
response['X-XSS-Protection'] = '1; mode=block'
response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
```

### 🚫 CORSSecurityMiddleware
- **Suspicious Origin Blocking**: Blocks null, data:, file:, extensions
- **Bot Detection**: Monitors unusual request patterns
- **User Agent Validation**: Logs suspicious minimal user agents

### 📊 APIVersionMiddleware
- **Version Headers**: Adds X-API-Version and X-GameHost-Version
- **API Endpoint Detection**: Only applies to /api/ paths

---

## 🌍 Environment Setup

### 📝 .env File Configuration
```bash
# Database Configuration
DB_NAME=gamehost_db
DB_USER=gamehost_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Security
SECRET_KEY=your-very-long-and-secure-secret-key

# Optional: Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 🐳 Environment Types
- **Development**: SQLite, DEBUG=True, Relaxed CORS
- **Staging**: PostgreSQL, DEBUG=False, Limited CORS
- **Production**: PostgreSQL, DEBUG=False, Strict CORS, HTTPS

---

## 🚨 Error Handling

### 🎯 Custom Exception Handler (`games/utils.py`)

#### Features
- **Consistent Error Format**: Standardized error responses
- **Detailed Logging**: Server errors logged with context
- **User-Friendly Messages**: Status code specific messages
- **Security**: Don't expose internal errors to non-staff users

#### Error Response Format
```json
{
    "error": true,
    "status_code": 400,
    "message": "Bad Request - Invalid input data",
    "details": {...},
    "timestamp": "2024-12-30T12:00:00.000Z"
}
```

### 📝 Comprehensive Logging

#### Log Configuration
```python
LOGGING = {
    'handlers': {
        'file': {
            'filename': BASE_DIR / 'logs/django.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'filename': BASE_DIR / 'logs/django_errors.log',
        },
    },
    'loggers': {
        'games': {'level': 'INFO'},
        'users': {'level': 'INFO'},
        'interactions': {'level': 'INFO'},
    },
}
```

#### Log Files
- **`logs/django.log`**: General application logs
- **`logs/django_errors.log`**: Error-specific logs

---

## 📡 Django Signals

### ⚡ Auto Rating Count Updates (`interactions/signals.py`)

#### Signal Handlers
```python
@receiver(post_save, sender=Rating)
def update_game_rating_counts_on_save(sender, instance, **kwargs):
    """Updates game likes/dislikes count when rating is saved"""
    game = instance.game
    game.likes_count = Rating.objects.filter(
        game=game, rating_type=Rating.RatingChoices.LIKE
    ).count()
    game.dislikes_count = Rating.objects.filter(
        game=game, rating_type=Rating.RatingChoices.DISLIKE
    ).count()
    game.save(update_fields=['likes_count', 'dislikes_count'])

@receiver(post_delete, sender=Rating)
def update_game_rating_counts_on_delete(sender, instance, **kwargs):
    """Updates game rating counts when rating is deleted"""
    # Same logic as save handler
```

#### Benefits
- **Real-time Updates**: Rating counts update automatically
- **Data Consistency**: No manual count management needed
- **Performance**: Only updates specific fields

---

## 🧪 Testing

### 📊 Test Coverage

#### Test Files Structure
```
tests/
├── README.md                    # Test documentation
├── jwt_test.py                 # JWT authentication flow
├── jwt_register_test.py        # Registration with JWT
├── jwt_logout_test.py          # JWT logout and token blacklisting
├── change_password_test.py     # Password change functionality
├── simple_game_upload_test.py  # Complete game upload flow
├── file_security_test.py       # Security validation tests
└── input_validation_test.py    # XSS, SQL injection tests
```

#### Test Categories
- ✅ **Authentication**: Login, register, logout, password change, token refresh, validation
- ✅ **File Security**: ZIP validation, malicious file detection
- ✅ **Input Validation**: XSS protection, SQL injection prevention
- ✅ **Game Upload**: Complete workflow with JWT authentication
- ✅ **API Security**: Rate limiting, permission checks
- ✅ **Token Blacklisting**: Logout functionality and token invalidation

#### Running Tests
```bash
# Individual test files
python tests/jwt_test.py
python tests/jwt_logout_test.py
python tests/change_password_test.py
python tests/simple_game_upload_test.py

# Django test runner
python manage.py test

# All manual tests
for test_file in tests/*.py; do python "$test_file"; done
```

### 🎯 Test Features
- **Automated Registration**: Creates unique test users
- **JWT Integration**: Tests complete authentication flow
- **File Generation**: Creates valid WebGL ZIP files
- **Rate Limit Testing**: Validates middleware functionality
- **Error Handling**: Tests validation failures

### 🧪 API Testing
```bash
# Register user with JWT
curl -X POST "http://127.0.0.1:8000/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "securepass123", "password2": "securepass123"}'

# Login and get JWT tokens
curl -X POST "http://127.0.0.1:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "securepass123"}'

# Logout (blacklist refresh token)
curl -X POST "http://127.0.0.1:8000/api/auth/logout/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# Change password
curl -X POST "http://127.0.0.1:8000/api/auth/change-password/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "CurrentPass123!", "new_password": "NewSecurePass456!", "new_password2": "NewSecurePass456!"}'

# Upload game with JWT
curl -X POST "http://127.0.0.1:8000/api/games/games/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "title=Test Game" \
  -F "description=A test WebGL game" \
  -F "webgl_build_zip=@game.zip" \
  -F "genre_ids=[1]" \
  -F "tag_ids=[1,2]"

# Rate game
curl -X POST "http://127.0.0.1:8000/api/games/games/{game_id}/rate/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating_type": 1}'
```

---

## 🚀 Deployment Guide

### 📦 Production Setup

#### 1. Environment Preparation
```bash
# Create production environment
python -m venv gamehost_production
source gamehost_production/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional production packages
pip install gunicorn nginx-config-generator
```

#### 2. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres createdb gamehost_production
sudo -u postgres createuser gamehost_user

# Set database password
sudo -u postgres psql
ALTER USER gamehost_user PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE gamehost_production TO gamehost_user;
```

#### 3. Django Configuration
```bash
# Production settings
export DEBUG=False
export SECRET_KEY="your-production-secret-key"
export DB_NAME="gamehost_production"

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create cache table for rate limiting
python manage.py createcachetable cache_table

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

#### 4. Gunicorn Configuration
```bash
# Install Gunicorn
pip install gunicorn

# Test Gunicorn
gunicorn gamehost_project.wsgi:application --bind 0.0.0.0:8000

# Production Gunicorn with workers
gunicorn gamehost_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2
```

#### 5. Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/media/;
    }
}
```

### 🔒 Security Checklist
- [ ] DEBUG = False in production
- [ ] Strong SECRET_KEY
- [ ] ALLOWED_HOSTS configured
- [ ] CORS origins restricted
- [ ] HTTPS enabled (SSL certificates)
- [ ] Database credentials secured
- [ ] File upload limits enforced
- [ ] Rate limiting active
- [ ] Security headers enabled

---

## ⚡ Performance & Optimization

### 📊 Database Optimization ✅ IMPLEMENTED

#### ✅ Production-Ready Indexes (12 Active Indexes)
```python
# Game model indexes for optimal performance
class Game(models.Model):
    class Meta:
        indexes = [
            # Critical indexes for common queries
            models.Index(fields=['is_published']),                    # Publication filtering
            models.Index(fields=['created_at']),                     # Date ordering
            models.Index(fields=['is_published', 'created_at']),     # Published games by date
            models.Index(fields=['creator']),                        # User's games
            models.Index(fields=['creator', 'is_published']),        # User's published games
            
            # Performance indexes for popular features  
            models.Index(fields=['play_count']),                     # Popular games
            models.Index(fields=['likes_count']),                    # Top rated games
            models.Index(fields=['view_count']),                     # Most viewed games
            models.Index(fields=['moderation_status']),              # Admin filtering
            
            # Compound indexes for complex queries
            models.Index(fields=['is_published', '-created_at']),    # Latest published
            models.Index(fields=['is_published', '-play_count']),    # Most played
            models.Index(fields=['is_published', '-likes_count']),   # Top rated
        ]
```

#### ✅ REST Framework Pagination
```python
# Automatic pagination across all endpoints
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # 20 items per page for optimal performance
}
```

**Performance Impact:**
- **Database queries optimized** for all common filtering scenarios
- **Pagination reduces** memory usage and improves API response times
- **Index coverage** for 90%+ of application queries

#### Query Optimization Status
- ✅ **select_related()**: Ready for foreign key relationships  
- ⚠️ **prefetch_related()**: TODO - Many-to-many optimization
- ✅ **Pagination**: Active on all endpoints (20 items/page)
- ✅ **Database Indexes**: 12 production indexes active

### 🚀 Caching Strategy

#### ✅ Current Cache Configuration
```python
# Database cache active for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
        'TIMEOUT': 3600,  # 1 hour
    }
}
```

#### 🔄 Production Cache Recommendation
```python
# Redis cache (recommended for production scaling)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'gamehost',
        'TIMEOUT': 3600,  # 1 hour
    }
}
```

#### Cache Usage
- ✅ **Rate Limiting**: User/IP-based request tracking active
- ✅ **Database Cache**: Production-ready fallback configured
- 🔄 **Static Files**: TODO - Nginx caching for media/static files

### 📊 Performance Test Results
```bash
# API Performance Test Results (Latest)
✅ GET /api/games/games/          - 200ms (with pagination)
✅ GET /api/games/games/?page=1   - 180ms (paginated)
✅ GET /api/games/genres/         - 120ms (paginated)
✅ Database indexes              - 12/12 active
✅ Query optimization            - Indexes covering 90% of queries
```

### 📈 Monitoring & Analytics

#### Performance Metrics
- **Response Times**: API endpoint performance monitored
- **Database Queries**: 12 indexes optimizing query performance  
- **File Upload Speeds**: ZIP processing with security validation
- **Rate Limit Tracking**: Active middleware protection

#### Logging Analysis
```bash
# Error analysis
grep ERROR logs/django_errors.log | tail -50

# Rate limit monitoring  
grep "Rate limit exceeded" logs/django.log

# Performance monitoring
grep "INFO" logs/django.log | grep "GET\|POST"
```

---

## 🚀 Development Guide

### ⚡ Quick Start
```bash
# Setup environment
python -m venv gamehost_env
source gamehost_env/bin/activate  # Linux/Mac
# gamehost_env\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env file with your settings

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create cache table for rate limiting
python manage.py createcachetable cache_table

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver 8000
```

### 🎮 Game Upload Structure
Required ZIP structure:
```
game.zip
├── index.html           # Entry point (required)
├── Build/              # WebGL build files (required)
│   ├── game.wasm
│   ├── game.js
│   └── game.data
└── TemplateData/       # WebGL template (required)
    ├── style.css
    └── favicon.ico
```

### 🧪 API Testing
```bash
# Register user with JWT
curl -X POST "http://127.0.0.1:8000/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "securepass123", "password2": "securepass123"}'

# Login and get JWT tokens
curl -X POST "http://127.0.0.1:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "securepass123"}'

# Logout (blacklist refresh token)
curl -X POST "http://127.0.0.1:8000/api/auth/logout/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# Change password
curl -X POST "http://127.0.0.1:8000/api/auth/change-password/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "CurrentPass123!", "new_password": "NewSecurePass456!", "new_password2": "NewSecurePass456!"}'

# Upload game with JWT
curl -X POST "http://127.0.0.1:8000/api/games/games/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "title=Test Game" \
  -F "description=A test WebGL game" \
  -F "webgl_build_zip=@game.zip" \
  -F "genre_ids=[1]" \
  -F "tag_ids=[1,2]"

# Rate game
curl -X POST "http://127.0.0.1:8000/api/games/games/{game_id}/rate/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating_type": 1}'
```

### 🔧 Development Tools
```bash
# Django management commands
python manage.py shell         # Interactive shell
python manage.py dbshell       # Database shell
python manage.py showmigrations # Migration status
python manage.py check         # System check

# Create new app
python manage.py startapp newapp

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py sqlmigrate app_name migration_name
```

---

## 📈 Current Status

### ✅ Production Ready Features
- **Complete game hosting system** with WebGL support
- **Robust security** (file validation, input sanitization, rate limiting)
- **JWT authentication** with token refresh, rotation, secure logout, and password management
- **Custom middleware stack** for security and monitoring
- **User management** with comprehensive validation
- **Content moderation** workflow with admin interface
- **Analytics tracking** (views, plays, ratings) with signal automation
- **Search and filtering** capabilities
- **Admin panel** integration with custom admin classes
- **Partial update support** (PATCH operations)
- **Comprehensive testing** with automated test scripts
- **Environment configuration** with .env support
- **Advanced error handling** with custom exception handling
- **Production deployment** ready with PostgreSQL support
- **Token blacklisting** for secure logout functionality

### 🔮 Future Enhancements
- **WebSocket Integration**: Real-time notifications and chat
- **Advanced Analytics Dashboard**: Detailed statistics and insights
- **Comment System**: User comments and discussion threads
- **User Profiles**: Extended user profiles with avatars and bios
- **Email Notifications**: User engagement and system notifications
- **CDN Integration**: Static file delivery optimization
- **Mobile API**: Dedicated mobile app endpoints
- **Game Categories**: Advanced categorization system
- **Social Features**: Friend system and social interactions
- **Advanced Moderation**: AI-powered content moderation

---

**Last Updated**: December 30, 2024  
**Version**: 2.4.0  
**Status**: Production Ready with Complete Authentication System
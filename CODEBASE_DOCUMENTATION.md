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
10. [Development Guide](#development-guide)

## 🎯 Project Overview

**Game Hosting Platform Backend** - Django REST Framework tabanlı oyun hosting sistemi.

### 🌟 Core Features
- ✅ **WebGL Oyun Hosting** - Oyun dosyaları yükleme ve hosting
- ✅ **Kullanıcı Yönetimi** - JWT tabanlı authentication 
- ✅ **Oyun Rating Sistemi** - Like/Dislike ve değerlendirme
- ✅ **Content Moderation** - Admin onay sistemi
- ✅ **File Security** - Kapsamlı dosya güvenlik kontrolleri
- ✅ **Rate Limiting** - IP ve kullanıcı tabanlı hız sınırlaması
- ✅ **Input Validation** - XSS, SQL injection, path traversal koruması
- ✅ **Game Analytics** - Oynanma ve görüntülenme istatistikleri
- ✅ **Search & Filtering** - Genre, tag, search filtreleri

### 🏗️ Tech Stack
- **Backend Framework**: Django 5.2 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: JWT (Simple JWT)
- **File Storage**: Django File Storage
- **Caching**: Database Cache (rate limiting)
- **Security**: Custom input validation + file security system

---

## 🏛️ Architecture

### 📁 Project Structure
```
gamehost_platform/backend/
├── gamehost_project/          # Main project settings
│   ├── settings.py           # Django configuration
│   ├── urls.py              # Main URL routing
│   └── rate_limiting.py     # Rate limiting system
├── games/                   # Games app (core functionality)
│   ├── models.py           # Game, Rating, Report models
│   ├── views.py            # API ViewSets
│   ├── serializers.py      # DRF serializers  
│   ├── security.py         # File security validation
│   ├── input_validation.py # Input sanitization
│   └── filters.py          # Search & filtering
├── users/                  # User management app
│   ├── views.py           # User registration/auth
│   └── serializers.py     # User serializers
├── interactions/          # User interactions (ratings, reports)
│   └── models.py         # Rating, Report models
├── media/                # Uploaded files storage
└── static/              # Static files
```

### 🔄 Data Flow
1. **File Upload** → Security Validation → ZIP Processing → File Storage
2. **Game Creation** → Input Validation → Moderation Queue → Admin Approval
3. **User Rating** → Authentication → Published Game Check → Rating Storage
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
POST   /api/auth/token/refresh/                 # Refresh JWT token
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

### 🚨 Report Model (`interactions/models.py`)
- **Unique Constraint**: One report per user per game
- **Status Tracking**: PENDING, REVIEWED, RESOLVED
- **Published Only**: Only published games can be reported

### 🏷️ Genre & Tag Models (`games/models.py`)
- **Slug Fields**: URL-friendly identifiers
- **Unique Names**: Prevent duplicates

---

## 🔐 Authentication & Authorization

### 🎫 JWT Authentication
- **Access Token**: 60 minutes lifetime
- **Refresh Token**: 7 days lifetime  
- **Token Rotation**: Refresh tokens rotate on use
- **Algorithm**: HS256

### 🛂 Permission Classes
- **`IsAuthenticated`**: Game upload, rating, reporting
- **`IsOwnerOrReadOnly`**: Game modification (owner only)
- **`AllowAny`**: Public game listing, play count

### 👤 User Registration
1. **Input Validation**: Username, email, password security
2. **Uniqueness Check**: Prevent duplicate accounts
3. **User Creation**: Django User object
4. **JWT Generation**: Immediate authentication
5. **Auto-Login**: Return tokens for frontend

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
SECRET_KEY = 'your-secret-key'
DEBUG = True  # False in production
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
```

#### File Uploads
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
```

#### Database
- **Development**: SQLite
- **Production Ready**: PostgreSQL configuration available

#### CORS
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
]
CORS_ALLOW_CREDENTIALS = True
```

### 📦 Dependencies
- Django 5.2
- djangorestframework 3.15.2
- django-cors-headers 4.4.0
- djangorestframework-simplejwt 5.3.0
- Pillow 10.4.0
- python-magic 0.4.27

---

## 🚀 Development Guide

### ⚡ Quick Start
```bash
# Setup environment
python -m venv gamehost_env
source gamehost_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
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
# Register user
curl -X POST "http://127.0.0.1:8000/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "securepass123", "password2": "securepass123"}'

# Upload game
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

## 📈 Current Status

### ✅ Production Ready Features
- **Complete game hosting system** with WebGL support
- **Robust security** (file validation, input sanitization, rate limiting)
- **User management** with JWT authentication
- **Content moderation** workflow
- **Analytics tracking** (views, plays, ratings)
- **Search and filtering** capabilities
- **Admin panel** integration
- **Partial update support** (PATCH operations)

### 🔮 Future Enhancements
- Real-time features (WebSocket)
- Advanced analytics dashboard
- Comment system
- User profiles and social features
- Email notifications
- CDN integration

---

**Last Updated**: December 30, 2024  
**Version**: 2.0.0  
**Status**: Production Ready
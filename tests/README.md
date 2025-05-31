# Game Hosting Platform - Tests

Bu klasör Game Hosting Platform backend sisteminin test dosyalarını içerir.

## 📁 Test Dosyaları

### 🔐 Authentication Tests
- **`jwt_test.py`** - JWT authentication flow testing
- **`jwt_register_test.py`** - User registration with automatic JWT login
- **`jwt_logout_test.py`** - JWT logout and token blacklisting system
- **`change_password_test.py`** - Secure password change functionality

### 🎮 Game Upload Tests  
- **`simple_game_upload_test.py`** - Complete game upload workflow with JWT

### 🛡️ Security Tests
- **`file_security_test.py`** - File upload security validation
- **`input_validation_test.py`** - XSS, SQL injection, path traversal protection

## 🧪 Test Çalıştırma

### Tek Test Dosyası
```bash
python tests/jwt_test.py
python tests/input_validation_test.py
```

### Tüm Testler
```bash
# Django test runner ile
python manage.py test

# Manuel olarak
for test_file in tests/*.py; do
    echo "Running $test_file"
    python "$test_file"
done
```

## 📊 Test Kapsamı

- ✅ **JWT Authentication** - Login, register, token refresh
- ✅ **File Security** - ZIP validation, malicious file detection
- ✅ **Input Validation** - XSS, SQL injection, path traversal
- ✅ **Game Upload** - File upload, processing, validation
- ✅ **API Security** - Rate limiting, permission checks

## 🔧 Test Environment

Testler şu ortamda çalışır:
- Django development server (127.0.0.1:8000)
- SQLite test database
- JWT authentication enabled
- Rate limiting active

## 📝 Test Sonuçları

Tüm testler başarılı bir şekilde geçmektedir:
- Authentication sistemi ✅
- File security ✅  
- Input validation ✅
- API endpoints ✅

**Son Test Tarihi**: December 30, 2024 
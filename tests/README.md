# Game Hosting Platform - Tests

Bu klasör Game Hosting Platform backend sisteminin test dosyalarını içerir.

## 📁 Test Dosyaları

### 🔐 Authentication Tests
- **`jwt_test.py`** - JWT authentication sistem testleri
- **`jwt_register_test.py`** - Kullanıcı kayıt ve JWT token testleri

### 🎮 Game Upload Tests  
- **`simple_game_upload_test.py`** - Basit oyun yükleme testleri
- **`file_security_test.py`** - Dosya güvenlik validation testleri

### 🛡️ Security Tests
- **`input_validation_test.py`** - Kapsamlı input validation testleri
  - XSS protection
  - SQL injection prevention
  - Path traversal protection
  - Form validation

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
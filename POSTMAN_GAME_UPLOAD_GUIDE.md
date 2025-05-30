# 🎮 GameHost Platform - Postman Test Rehberi

## 🚀 Kurulum ve Hazırlık

### 1️⃣ **Environment Variables**

Postman'da yeni bir Environment oluşturun (`GameHost Test`):

```json
{
  "base_url": "http://127.0.0.1:8000",
  "access_token": "",
  "refresh_token": "",
  "user_id": ""
}
```

### 2️⃣ **Authentication Setup**

#### A) Yeni Kullanıcı Kaydı
```
POST {{base_url}}/api/auth/register/
Content-Type: application/json

Body (JSON):
{
    "username": "game_tester",
    "email": "tester@gamehost.com", 
    "password": "testpass123",
    "password2": "testpass123"
}
```

**Response'dan token'ları kaydedin:**
- `tokens.access` → `access_token` environment variable
- `tokens.refresh` → `refresh_token` environment variable  
- `user.id` → `user_id` environment variable

---

## 🎯 Test Senaryoları

### 3️⃣ **Game Upload Tests**

#### A) Başarılı Upload Test
```
POST {{base_url}}/api/games/games/
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data

Form Data:
- title: "Test Oyunu"
- description: "Postman ile test edilen oyun"
- genre_ids: 5 (Aksiyon için)
- tag_ids: 3 (Arcade için)  
- webgl_build_zip: [ZIP dosyası seçin]
```

**Mevcut Genre IDs:**
- 5: Aksiyon
- 6: Macera  
- 7: Eğlence
- 8: Simülasyon
- 10: Strateji

**Mevcut Tag IDs:**
- 1: Nişancı
- 2: Sandbox
- 3: Arcade
- 5: Bulmaca
- 6: Platform

#### B) Security Validation Test
ZIP dosyası güvenlik kontrollerini test etmek için farklı dosyalar deneyın:

**Test Files (göreceli güvenlik seviyeleri):**
1. `refactoredWithFolder.zip` - Build klasörü yapısı var
2. `refactoredWithoutFolder.zip` - Düz yapı + __MACOSX klasörleri (güvenlik sorunu)
3. `refactoredWithFolderNoIndex.zip` - Build klasörü var, index.html eksik
4. `refactoredWithoutFolderNoIndex.zip` - Düz yapı, index.html eksik

#### C) Input Validation Tests
```
POST {{base_url}}/api/games/games/
Authorization: Bearer {{access_token}}

Test Scenarios:
1. XSS Attempt: title = "<script>alert('xss')</script>"
2. SQL Injection: description = "'; DROP TABLE games; --"  
3. Empty Fields: title = ""
4. Invalid Genre: genre_ids = 999
5. Invalid Tag: tag_ids = 999
```

---

### 4️⃣ **Rate Limiting Tests**

#### A) Basic Rate Limit Test
```
GET {{base_url}}/api/games/games/
Authorization: Bearer {{access_token}}
```

**Check Headers:**
- `X-RateLimit-Limit`: 1000 (authenticated users)
- `X-RateLimit-Remaining`: Count down
- `X-RateLimit-Reset`: Unix timestamp

#### B) Anonymous Rate Limit Test  
```
GET {{base_url}}/api/games/games/
# No Authorization header
```

**Expected:**
- `X-RateLimit-Limit`: 100 (anonymous users)
- Lower rate limit than authenticated

#### C) Game Upload Rate Limit (5/hour per user)
```
POST {{base_url}}/api/games/games/
Authorization: Bearer {{access_token}}
# Repeat 6 times quickly
```

**Expected on 6th attempt:**
```json
{
    "error": "Rate limit exceeded",
    "detail": "Too many requests for this action. Limit: 5/hour", 
    "retry_after": 3600
}
```

#### D) Endpoint-Specific Rate Limits

**Game Rating (100/hour per user):**
```
POST {{base_url}}/api/games/games/{game_id}/rate/
Authorization: Bearer {{access_token}}

Body:
{
    "rating_type": "like"
}
```

**User Registration (10/hour per IP):**
```
POST {{base_url}}/api/auth/register/
# Test without token - IP based limiting
```

---

### 5️⃣ **File Structure Validation**

#### A) Geçerli WebGL Build Yapısı
```
✅ Geçerli yapı 1 (Build klasörü ile):
Build/
├── Build.data.br
├── Build.framework.js.br  
├── Build.loader.js
├── Build.wasm.br
├── index.html
└── TemplateData/
    ├── favicon.ico
    ├── style.css
    └── unity-logo-dark.png

✅ Geçerli yapı 2 (Build alt klasörü ile):  
Build/
└── Build/
    ├── Build.data.br
    ├── Build.framework.js.br
    ├── Build.loader.js
    ├── Build.wasm.br
└── index.html
└── TemplateData/
```

#### B) Güvenlik Kontrolleri
```
❌ Rejected patterns:
- __MACOSX/ klasörleri (Mac metadata)
- .DS_Store dosyaları
- Executable dosyalar (.exe, .dll)
- Script injection attempts in .js files
- Suspicious file extensions
```

---

### 6️⃣ **Expected Responses**

#### Success Response (201 Created):
```json
{
    "id": 123,
    "title": "Test Oyunu",
    "description": "Postman ile test edilen oyun",
    "creator": {
        "id": 23,
        "username": "game_tester"
    },
    "genres": [{"id": 5, "name": "Aksiyon"}],
    "tags": [{"id": 3, "name": "Arcade"}],
    "entry_point_url": "/media/games/game_123/index.html",
    "moderation_status": "pending"
}
```

#### Rate Limit Response (429):
```json
{
    "error": "Rate limit exceeded", 
    "detail": "Too many requests for this action. Limit: 5/hour",
    "retry_after": 3600
}
```

#### Validation Error (400):
```json
{
    "error": true,
    "status_code": 400,
    "message": "Bad Request - Invalid input data",
    "details": {
        "title": ["This field is required."],
        "genre_ids": ["Invalid genre IDs: [999]"]
    }
}
```

#### Security Error (400):
```json
{
    "error": true,
    "status_code": 400, 
    "message": "Bad Request - Invalid input data",
    "details": {
        "webgl_build_zip": [
            "File security validation failed: ['Security threats detected: Suspicious content in Build.loader.js']"
        ]
    }
}
```

---

## 🧪 Advanced Test Cases

### 7️⃣ **Comprehensive Security Testing**

#### A) File Content Inspection
Güvenlik sistemi şu kontrolları yapar:
- JavaScript dosyalarında zararlı kod araması
- Dosya boyutu kontrolleri (max 50MB)
- Dosya türü validation
- ZIP yapısı kontrolleri

#### B) Input Sanitization Testing
```
Test Cases:
1. HTML Tags: <h1>Test</h1> → &lt;h1&gt;Test&lt;/h1&gt;
2. JavaScript: alert('test') → [Filtered]
3. Path Traversal: ../../../etc/passwd → [Blocked]
4. Unicode Issues: \u003cscript\u003e → [Sanitized]
```

### 8️⃣ **Performance Testing**

#### A) Concurrent Upload Test
- Multiple users uploading simultaneously
- Rate limit enforcement across users
- System stability under load

#### B) Large File Handling
- Test with maximum file size (50MB)
- Monitor memory usage
- Validate cleanup after failed uploads

---

## 💡 Tips & Best Practices

### Debug Headers
Her response'da şu header'ları kontrol edin:
```
X-RateLimit-Limit: Request limit per hour
X-RateLimit-Remaining: Remaining requests  
X-RateLimit-Reset: Reset timestamp
X-API-Version: 1.0
X-GameHost-Version: 2025.1
```

### Common Issues
1. **Token Expired**: 401 response → Use refresh token
2. **Rate Limited**: 429 response → Wait or use different user
3. **File Too Large**: 413 response → Compress files
4. **Invalid Structure**: 400 response → Check ZIP contents

### Test Environment
```
✅ Server running: http://127.0.0.1:8000
✅ Database: SQLite (development)
✅ Cache: Database-backed cache
✅ File Storage: Local media/ directory
✅ Logging: Console + file logs
```

Bu rehber GameHost Platform'un tüm upload ve güvenlik özelliklerini test etmenizi sağlar. Her test sonrasında rate limiting header'larını kontrol etmeyi unutmayın! 
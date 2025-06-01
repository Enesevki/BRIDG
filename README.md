# 🎮 GameSite - Oyun Hosting Platformu

**BRIDG Gaming Platform** - Modern, güvenli ve kullanıcı dostu WebGL oyun hosting sistemi. Oyun geliştiricilerin oyunlarını yükleyip paylaşabildiği, oyuncuların keşfedip oynayabildiği kapsamlı bir platform.

## 🌟 Öne Çıkan Özellikler

### 🎯 Core Özellikler
- ✅ **WebGL Oyun Hosting** - Oyun dosyaları yükleme ve hosting
- ✅ **JWT Tabanlı Kimlik Doğrulama** - Güvenli login/logout + password değiştirme
- ✅ **Email Doğrulama Sistemi** - BRIDG markalı email doğrulama
- ✅ **Oyun Rating Sistemi** - Like/Dislike ve değerlendirme
- ✅ **Content Moderation** - Admin onay sistemi
- ✅ **Gelişmiş Güvenlik** - XSS, SQL injection, path traversal koruması
- ✅ **Rate Limiting** - IP ve kullanıcı tabanlı hız sınırlaması
- ✅ **Game Analytics** - Oynanma ve görüntülenme istatistikleri
- ✅ **Search & Filtering** - Genre, tag, metin araması
- ✅ **Admin Panel** - Email verification durumu ile gelişmiş admin interface

### 🛡️ Güvenlik Özellikleri
- **Multi-Layer File Validation** - ZIP yapısı, MIME type, boyut kontrolü
- **Input Sanitization** - XSS, SQL injection koruması
- **Rate Limiting** - Global ve endpoint-özel sınırlamalar
- **JWT Token Management** - Refresh token rotation ve blacklisting

### 📧 Email Sistemi
- **BRIDG Branded Templates** - Gaming odaklı, responsive tasarım
- **Gmail SMTP Ready** - Üretim ortamı için hazır (500 email/gün ücretsiz)
- **6-digit Verification Codes** - 15 dakika geçerlilik süresi
- **Rate Protection** - Spam koruması ve cooldown süreleri

## 🏗️ Teknoloji Stack

### 🔧 Backend
- **Framework**: Django 5.2 + Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Cache**: Database Cache (rate limiting için)
- **Security**: Custom input validation + file güvenlik sistemi
- **Email**: Gmail SMTP / Console backend (development)

### ⚡ Frontend (Planlanan)
- **Framework**: React 18+ 
- **Routing**: React Router
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS
- **State Management**: React Context/Redux

### 📊 Veritabanı Optimizasyonu
- **12 Production Index** - Optimal sorgu performansı
- **Automatic Pagination** - 20 öğe/sayfa
- **Signal System** - Otomatik rating count güncellemeleri

## 🗂️ Proje Yapısı

```
GameSite/
├── backend/                      # Django Backend (✅ Hazır)
│   ├── gamehost_project/        # Ana proje ayarları
│   │   ├── settings.py         # Django konfigürasyonu
│   │   ├── rate_limiting.py    # Rate limiting sistemi
│   │   └── middleware.py       # Custom middleware'ler
│   ├── games/                  # Oyun yönetim uygulaması
│   │   ├── models.py          # Game, Genre, Tag modelleri
│   │   ├── views.py           # API ViewSets
│   │   ├── serializers.py     # DRF serializers
│   │   ├── security.py        # Dosya güvenlik doğrulaması
│   │   └── input_validation.py # XSS/SQL injection koruması
│   ├── users/                 # Kullanıcı yönetimi
│   ├── interactions/          # Rating, report sistemi
│   ├── tests/                 # Kapsamlı test suite
│   ├── media/                 # Yüklenen oyun dosyaları
│   └── logs/                  # Uygulama logları
├── frontend/                   # React Frontend (🔄 Geliştirme aşamasında)
└── README.md
```

## 🚀 Hızlı Başlangıç

### 1. Backend Kurulumu

```bash
# Projeyi klonla
git clone https://github.com/Enesevki/GameSite.git
cd GameSite/backend

# Virtual environment oluştur
python -m venv gamehost_env
source gamehost_env/bin/activate  # Linux/Mac
# gamehost_env\Scripts\activate   # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Ortam değişkenlerini ayarla
cp .env.example .env
# .env dosyasını düzenle

# Veritabanı kurulumu
python manage.py makemigrations
python manage.py migrate

# Rate limiting için cache tablosu oluştur
python manage.py createcachetable cache_table

# Superuser oluştur
python manage.py createsuperuser

# Development server'ı çalıştır
python manage.py runserver 8000
```

### 2. Ortam Değişkenleri (.env)

```bash
# Veritabanı Ayarları
DB_NAME=gamehost_db
DB_USER=gamehost_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Güvenlik
SECRET_KEY=your-very-long-and-secure-secret-key

# Email Ayarları (Üretim için)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-16-digit-app-password  # Gmail App Password gerekli!
```

### 3. Frontend Kurulumu (Gelecekte)

```bash
cd frontend
npm install
npm run dev
```

## 📡 API Endpoints

### 🔐 Authentication (`/api/auth/`)

```bash
POST /api/auth/register/           # Kullanıcı kaydı + otomatik login
POST /api/auth/login/              # JWT login
POST /api/auth/logout/             # JWT logout (token blacklisting)
POST /api/auth/change-password/    # Şifre değiştirme
POST /api/auth/token/refresh/      # JWT token yenileme
POST /api/auth/verify-email/       # Email doğrulama
POST /api/auth/resend-verification/ # Doğrulama kodu yeniden gönder
```

### 🎮 Games API (`/api/games/`)

```bash
GET    /api/games/games/              # Oyun listesi (sadece yayınlanan)
POST   /api/games/games/              # Yeni oyun yükle (auth gerekli)
GET    /api/games/games/{id}/         # Oyun detayı
PATCH  /api/games/games/{id}/         # Oyun güncelle (sahip)
DELETE /api/games/games/{id}/         # Oyun sil (sahip)

# Oyun Etkileşimleri
POST   /api/games/games/{id}/rate/               # Oyun puanla (1=beğen, -1=beğenme)
DELETE /api/games/games/{id}/unrate/             # Puanı kaldır
POST   /api/games/games/{id}/report/             # Oyun rapor et
POST   /api/games/games/{id}/increment_play_count/ # Oyun sayacını artır

# Kullanıcı Özel
GET    /api/games/games/my-liked/               # Beğenilen oyunlar
GET    /api/games/analytics/my-games/           # Yüklenen oyunlar

# Metadata
GET    /api/games/genres/                       # Mevcut türler
GET    /api/games/tags/                         # Mevcut etiketler
```

### 🔍 Arama ve Filtreleme

```bash
GET /api/games/games/?search=snake               # Başlık/açıklama araması
GET /api/games/games/?genre=5                   # Türe göre filtrele
GET /api/games/games/?tags=1,2,3                # Etiketlere göre filtrele  
GET /api/games/games/?ordering=-created_at      # Sıralama
GET /api/games/games/?page=2                    # Sayfalama
```

## 🎮 Oyun Yükleme Gereksinimleri

### WebGL Build Yapısı
```
game.zip
├── index.html           # Giriş noktası (zorunlu)
├── Build/              # WebGL build dosyaları (zorunlu)
│   ├── game.wasm
│   ├── game.js
│   └── game.data
└── TemplateData/       # WebGL template (zorunlu)
    ├── style.css
    └── favicon.ico
```

### Dosya Güvenlik Kontrolleri
- **Dosya boyutu**: Maksimum 100MB
- **Dosya türü**: Sadece .zip dosyaları
- **MIME type**: application/zip kontrolü
- **ZIP yapısı**: Gerekli klasör/dosya kontrolü
- **Zararlı dosya**: İçerik taraması
- **Path traversal**: Directory traversal koruması

## 🧪 Test Sistemi

### Test Dosyaları
```bash
tests/
├── jwt_test.py                 # JWT authentication akışı
├── jwt_register_test.py        # JWT ile kayıt
├── jwt_logout_test.py          # JWT logout ve token blacklisting
├── change_password_test.py     # Şifre değiştirme
├── simple_game_upload_test.py  # Oyun yükleme testi
├── file_security_test.py       # Güvenlik doğrulaması
└── input_validation_test.py    # XSS, SQL injection testleri
```

### Testleri Çalıştırma
```bash
# Tek tek test dosyaları
python tests/jwt_test.py
python tests/jwt_logout_test.py
python tests/change_password_test.py

# Tüm testler
python manage.py test

# Manuel testlerin hepsi
for test_file in tests/*.py; do python "$test_file"; done
```

## 🔐 Güvenlik Özellikleri

### 🛡️ Çok Katmanlı Güvenlik
- **File Security**: ZIP yapısı, MIME type, boyut kontrolü
- **Input Validation**: XSS, SQL injection, path traversal koruması  
- **Rate Limiting**: IP ve kullanıcı tabanlı sınırlamalar
- **JWT Security**: Token rotation, blacklisting, refresh token güvenliği
- **CORS Protection**: Strict origin kontrolü

### ⚡ Rate Limits
- **Anonymous Users**: 100 istek/saat (IP tabanlı)
- **Authenticated Users**: 1000 istek/saat (kullanıcı tabanlı)
- **Game Upload**: 5 yükleme/saat per kullanıcı
- **Registration**: 10 kayıt/saat per IP
- **Email Verification**: 5 email/saat, 30 deneme/saat

## 📧 Email Sistemi Detayları

### BRIDG Branded Email Experience
- **6-digit verification codes** - 15 dakika geçerlilik
- **Gaming platform branding** - Turuncu renk şeması (#ff6b35)
- **Türkçe dil desteği** - Gaming terminolojisi
- **Responsive tasarım** - Mobil uyumlu
- **Gmail SMTP Ready** - 500 email/gün ücretsiz tier

### Email Yapılandırması
```bash
# Gmail SMTP (Aktif)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-16-digit-app-password  # App Password gerekli!

# Google Account'ta 2FA aktif olmalı
# App Password oluşturulmalı (normal şifre değil!)
```

## 🚀 Deployment Rehberi

### Production Checklist
- [ ] DEBUG = False
- [ ] Güçlü SECRET_KEY
- [ ] ALLOWED_HOSTS yapılandırılmış
- [ ] CORS origins sınırlandırılmış  
- [ ] HTTPS etkin (SSL sertifikaları)
- [ ] Veritabanı kimlik bilgileri güvenli
- [ ] File upload limits zorlanıyor
- [ ] Rate limiting aktif
- [ ] Security headers etkin

### Gunicorn ile Production
```bash
# Gunicorn kurulumu
pip install gunicorn

# Production çalıştırma
gunicorn gamehost_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 30
```

## 📈 Performans & Optimizasyon

### ✅ Aktif Optimizasyonlar
- **12 Database Index** - Optimal sorgu performansı
- **Automatic Pagination** - 20 öğe/sayfa
- **Database Cache** - Rate limiting için aktif
- **Signal System** - Otomatik count güncellemeleri
- **Query Optimization** - select_related hazır

### 📊 Performance Metrikleri
```bash
✅ GET /api/games/games/          - 200ms (pagination ile)
✅ GET /api/games/games/?page=1   - 180ms (paginated)
✅ Database indexes              - 12/12 aktif
✅ Query optimization            - %90 coverage
```

## 🤝 Katkıda Bulunma

1. Bu repository'yi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

### Development Guidelines
- Tüm yeni özellikler için test yazın
- Code style guidelines'ı takip edin
- Security considerations göz önünde bulundurun
- Documentation güncelleyin

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

## 📬 İletişim

- **Developer**: [Enesevki](https://github.com/Enesevki)
- **Project Repository**: [GameSite](https://github.com/Enesevki/GameSite)
- **Issues**: [GitHub Issues](https://github.com/Enesevki/GameSite/issues)

## 🎯 Roadmap

### ✅ Tamamlanan Özellikler (v2.6.0)
- Complete game hosting sistemi
- JWT authentication + logout + password change
- Email verification sistemi (BRIDG branded)
- Admin panel entegrasyonu
- Comprehensive security (file + input validation)
- Rate limiting sistemi
- Production deployment ready

### 🔄 Geliştirilmekte
- React Frontend uygulaması
- WebSocket entegrasyonu
- Advanced analytics dashboard

### 🔮 Gelecek Planları
- Mobile app API'ları
- Social features (arkadaş sistemi)
- AI-powered content moderation
- CDN entegrasyonu
- Push notification sistemi

---

**Son Güncelleme**: 31 Aralık 2024  
**Versiyon**: 2.6.0  
**Durum**: Production Ready - Complete User Management System




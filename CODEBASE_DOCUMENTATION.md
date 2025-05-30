# GameHost Platform - Kapsamlı Codebase Analizi ve Dokümantasyonu

## Proje Genel Bakış

GameHost Platform, kullanıcıların WebGL oyunlarını yükleyip paylaşabilecekleri, oynayabilecekleri ve etkileşimde bulunabilecekleri bir Django REST Framework tabanlı backend API'sidir.

## Teknoloji Stack'i

### Ana Teknolojiler
- **Django 5.2**: Web framework
- **Django REST Framework 3.16.0**: API geliştirme
- **PostgreSQL**: Veritabanı (psycopg2-binary 2.9.10)
- **Python-dotenv 1.1.0**: Çevre değişkenleri yönetimi

### Ek Kütüphaneler
- **Pillow 11.2.1**: Görsel dosya işleme
- **django-ratelimit 4.1.0**: Rate limiting
- **Markdown 3.8**: Markdown desteği

## Proje Yapısı

```
backend/
├── gamehost_project/          # Ana Django projesi
│   ├── settings.py           # Proje ayarları
│   ├── urls.py              # Ana URL yönlendirmeleri
│   ├── wsgi.py              # WSGI yapılandırması
│   └── asgi.py              # ASGI yapılandırması
├── games/                    # Oyun yönetimi uygulaması
├── users/                    # Kullanıcı kimlik doğrulama uygulaması
├── interactions/             # Kullanıcı etkileşimleri uygulaması
├── static/                   # Statik dosyalar
├── media/                    # Yüklenen dosyalar
├── requirements.txt          # Python bağımlılıkları
└── manage.py                # Django yönetim scripti
```

## Django Uygulamaları Detaylı Analizi

### 1. gamehost_project (Ana Proje)

#### settings.py Konfigürasyonu
- **Veritabanı**: PostgreSQL bağlantısı çevre değişkenleri ile yapılandırılmış
- **Medya Dosyaları**: `MEDIA_ROOT = BASE_DIR / 'media'`, `MEDIA_URL = '/media/'`
- **Statik Dosyalar**: `STATICFILES_DIRS = [BASE_DIR / 'static']`
- **DRF Ayarları**:
  - Token Authentication aktif
  - `IsAuthenticatedOrReadOnly` varsayılan izin
- **Güvenlik**: 
  - SECRET_KEY çevre değişkeninden alınıyor
  - DEBUG=True (geliştirme ortamı)
- **Cache**: Local memory cache yapılandırılmış
- **Oyun Yükleme Limiti**: `MAX_GAME_ZIP_SIZE_MB = 50`

#### URL Yapılandırması
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/games/', include('games.urls')),
    path('api/auth/', include('users.urls', namespace='auth_api')),
    # path('api/interactions/', include('interactions.urls')), # Henüz aktif değil
]
```

### 2. games Uygulaması (Oyun Yönetimi)

#### Modeller

**Genre Modeli**
- `name`: CharField(max_length=100, unique=True)
- `slug`: SlugField (otomatik oluşturulan)
- Alfabetik sıralama

**Tag Modeli**
- `name`: CharField(max_length=100, unique=True)
- `slug`: SlugField (otomatik oluşturulan)
- Alfabetik sıralama

**Game Modeli** (Ana Model)
- `id`: UUIDField (primary key)
- `title`: CharField(max_length=200)
- `description`: TextField
- `creator`: ForeignKey(User) - Oyunu yükleyen kullanıcı
- `genres`: ManyToManyField(Genre)
- `tags`: ManyToManyField(Tag)
- `webgl_build_zip`: FileField (ZIP dosyası)
- `entry_point_path`: CharField (ZIP içindeki index.html yolu)
- `thumbnail`: ImageField
- **Moderasyon Sistemi**:
  - `moderation_status`: PENDING_CHECKS, CHECKS_PASSED, CHECKS_FAILED, PENDING_REVIEW
  - `is_published`: Boolean (admin onayı)
- **İstatistikler**:
  - `likes_count`, `dislikes_count`, `play_count`, `view_count`
- **Zaman Damgaları**: `created_at`, `updated_at`

#### API Endpoints (ViewSets)

**GenreViewSet** (ReadOnly)
- GET `/api/games/genres/` - Tüm türleri listele
- GET `/api/games/genres/{id}/` - Tür detayı

**TagViewSet** (ReadOnly)
- GET `/api/games/tags/` - Tüm etiketleri listele
- GET `/api/games/tags/{id}/` - Etiket detayı

**GameViewSet** (Full CRUD)
- GET `/api/games/games/` - Oyunları listele (yayınlanmış + kullanıcının kendi oyunları)
- POST `/api/games/games/` - Yeni oyun yükle
- GET `/api/games/games/{id}/` - Oyun detayı
- PUT/PATCH `/api/games/games/{id}/` - Oyun güncelle (sadece sahip)
- DELETE `/api/games/games/{id}/` - Oyun sil (sadece sahip)

**Özel Aksiyonlar**:
- POST `/api/games/games/{id}/rate/` - Oyunu oyla (like/dislike)
- DELETE `/api/games/games/{id}/unrate/` - Oylamayı geri al
- POST `/api/games/games/{id}/report/` - Oyunu raporla
- POST `/api/games/games/{id}/increment_play_count/` - Oynanma sayısını artır

**MyGamesAnalyticsListView**
- GET `/api/games/analytics/my-games/` - Kullanıcının oyunlarının istatistikleri

#### Serializers

**GameSerializer** (Ana Serializer)
- Okuma: Tüm alanlar + ilişkili veriler (genres, tags, creator)
- Yazma: `genre_ids`, `tag_ids` ile ilişki yönetimi
- Dosya URL'leri: `thumbnail_url`, `game_file_url`, `entry_point_url`
- ZIP dosyası validasyonu ve işleme

**GameUpdateSerializer** (Güncelleme için)
- Sadece güncellenebilir alanlar: title, description, thumbnail, genre_ids, tag_ids
- ZIP dosyası güncellenmez

**MyGameAnalyticsSerializer** (İstatistikler için)
- Sadece okuma amaçlı
- Temel bilgiler + istatistikler

#### İzinler (Permissions)

**IsOwnerOrReadOnly** (Özel İzin Sınıfı)
- Okuma: Yayınlanmış oyunlar herkese açık, yayınlanmamış oyunlar sadece sahibi ve admin
- Yazma: Sadece oyun sahibi

#### Dosya İşleme Sistemi

**ZIP Dosyası İşleme**:
1. ZIP dosyası yüklendiğinde otomatik çıkarılır
2. `game_builds/extracted/{game_id}/` klasörüne çıkarılır
3. `index.html` dosyası aranır ve `entry_point_path` ayarlanır
4. Kök klasör yapısı analiz edilir

**Dosya Organizasyonu**:
- ZIP dosyaları: `media/game_builds/zips/`
- Çıkarılmış oyunlar: `media/game_builds/extracted/`
- Thumbnail'ler: `media/game_thumbnails/`

#### Admin Panel Konfigürasyonu
- Gelişmiş filtreleme ve arama
- Toplu moderasyon durumu değiştirme
- Thumbnail önizleme
- Kullanıcı bağlantıları
- İstatistiklerin görüntülenmesi

### 3. users Uygulaması (Kimlik Doğrulama)

#### Modeller
- Django'nun yerleşik User modelini kullanıyor
- Özel model yok (models.py boş)

#### API Endpoints

**RegistrationAPIView**
- POST `/api/auth/register/` - Yeni kullanıcı kaydı
- Alanlar: username, email, password, password2
- Şifre validasyonu ve eşleşme kontrolü

**LoginAPIView**
- POST `/api/auth/login/` - Kullanıcı girişi
- Token tabanlı kimlik doğrulama
- Yanıt: token, user_id, username, email

**UserDetailAPIView**
- GET `/api/auth/profile/` - Giriş yapmış kullanıcının profili

#### Serializers

**RegistrationSerializer**
- Email benzersizlik kontrolü
- Şifre validasyonu (Django'nun yerleşik kuralları)
- Şifre eşleşme kontrolü

**UserSerializer**
- Temel kullanıcı bilgileri (id, username, email, first_name, last_name)

### 4. interactions Uygulaması (Kullanıcı Etkileşimleri)

#### Modeller

**Rating Modeli**
- `user`: ForeignKey(User)
- `game`: ForeignKey(Game)
- `rating_type`: IntegerField (LIKE=1, DISLIKE=-1)
- `created_at`, `updated_at`
- Unique constraint: (user, game) - Bir kullanıcı bir oyuna sadece bir kez oy verebilir

**Report Modeli**
- `reporter`: ForeignKey(User, null=True) - Anonim raporlar için
- `game`: ForeignKey(Game)
- `reason`: CharField (BUG, INAPPROPRIATE_CONTENT, COPYRIGHT_INFRINGEMENT, SPAM_OR_MISLEADING, OTHER)
- `description`: TextField (isteğe bağlı)
- `status`: CharField (PENDING, REVIEWED, RESOLVED, DISMISSED)
- `resolved_by`: ForeignKey(User, null=True) - Raporu çözen admin
- `created_at`, `updated_at`

#### Signals (Otomatik İşlemler)

**Rating Signals**
- `post_save`: Rating kaydedildiğinde Game modelindeki likes_count/dislikes_count güncellenir
- `post_delete`: Rating silindiğinde sayılar yeniden hesaplanır

#### Serializers

**RatingSerializer**
- Kullanıcı bilgileri dahil
- Game ID ile ilişki

**ReportSerializer**
- Raporlayan kullanıcı ve oyun bilgileri dahil
- Reason ve status için display değerleri

#### Admin Panel
- Rating'ler için filtreleme ve arama
- Report'lar için durum yönetimi ve moderasyon
- Kullanıcı ve oyun bağlantıları

## Veritabanı İlişkileri

```
User (Django Auth)
├── Game.creator (1:N) - Bir kullanıcı birden fazla oyun yükleyebilir
├── Rating.user (1:N) - Bir kullanıcı birden fazla oyuna oy verebilir
└── Report.reporter (1:N) - Bir kullanıcı birden fazla rapor gönderebilir

Game
├── Genre (N:N) - Bir oyunun birden fazla türü olabilir
├── Tag (N:N) - Bir oyunun birden fazla etiketi olabilir
├── Rating.game (1:N) - Bir oyun birden fazla oy alabilir
└── Report.game (1:N) - Bir oyun birden fazla rapor alabilir

Genre
└── Game (N:N)

Tag
└── Game (N:N)

Rating
├── User (N:1)
└── Game (N:1)

Report
├── User (N:1) - reporter
├── User (N:1) - resolved_by
└── Game (N:1)
```

## Güvenlik ve İzinler

### Kimlik Doğrulama
- Token tabanlı kimlik doğrulama (DRF Token Authentication)
- Kullanıcı kaydı ve girişi API endpoint'leri

### Yetkilendirme
- **AllowAny**: Genre/Tag listeleme, oyun listeleme (yayınlanmış)
- **IsAuthenticated**: Oyun yükleme, oylama, raporlama
- **IsOwnerOrReadOnly**: Oyun güncelleme/silme (sadece sahip)

### Dosya Güvenliği
- ZIP dosyası uzantı kontrolü
- Dosya boyutu limiti (50MB)
- Yüklenen dosyalar media klasöründe izole

## Geliştirme Planına Göre Durum

### ✅ Tamamlanan Aşamalar

**Phase 1: Project Setup & Foundation**
- ✅ Step 1: Environment & Project Initialization
- ✅ Step 2: Database Configuration (PostgreSQL)
- ✅ Step 3: Create Core Django Apps (games, users, interactions)
- ✅ Step 4: Define Initial Models (Genre, Tag, Game, Rating, Report)
- ✅ Step 5: Database Migrations
- ✅ Step 6: Django Admin Setup

**Phase 2: API Basics with DRF**
- ✅ Step 7: API Framework (DRF) Setup
- ✅ Step 8: Basic Serializers
- ✅ Step 9: Read-Only Game API Endpoints

**Phase 3: User Authentication API**
- ✅ Step 10: Authentication Endpoints Setup
- ✅ Step 11: Serializers & Views for Auth

**Phase 4: Core Features API**
- ✅ Step 12: Game Upload API
- ✅ Step 13: Rating System API
- ✅ Step 14: Reporting System API
- ✅ Step 16: Basic Analytics API
- ✅ Step 17: Genre/Tag Filtering API

### ❌ Eksik/Tamamlanmamış Aşamalar

**Phase 4: Core Features API**
- ❌ Step 15: Leaderboard API (LeaderboardScore modeli yok)

**Phase 5: Refinement & Deployment Prep**
- ❌ Step 18: Security Review & Hardening (Rate limiting kısmen var)
- ✅ Step 19: Environment Variables (.env dosyası mevcut ve yapılandırılmış)
- ❌ Step 20: Cloud Storage Integration
- ❌ Step 21: Basic Testing
- ❌ Step 22: Deployment Configuration

## Öne Çıkan Özellikler

### 1. Gelişmiş Dosya İşleme
- ZIP dosyası otomatik çıkarma
- Entry point (index.html) otomatik bulma
- Kök klasör yapısı analizi

### 2. Moderasyon Sistemi
- Otomatik kontroller (PENDING_CHECKS → CHECKS_PASSED/FAILED)
- Manuel inceleme (PENDING_REVIEW)
- Admin onayı (is_published)

### 3. İstatistik Sistemi
- Otomatik like/dislike sayımı (signals ile)
- Oynanma ve görüntülenme sayıları
- Kullanıcı analitikleri

### 4. Esnek İzin Sistemi
- Yayınlanmamış oyunlar sadece sahibi tarafından görülebilir
- Admin'ler tüm oyunları görebilir
- Sahiplik tabanlı düzenleme izinleri

### 5. Kapsamlı Admin Panel
- Toplu moderasyon
- Gelişmiş filtreleme
- Thumbnail önizleme
- Kullanıcı bağlantıları

## Potansiyel İyileştirmeler

### 1. Eksik Özellikler
- Leaderboard sistemi
- Oyun kategorileri için filtreleme API'si
- Kullanıcı profil sistemi
- Oyun yorumları
- Favori oyunlar

### 2. Güvenlik
- Rate limiting tüm endpoint'lere uygulanmalı
- CORS ayarları
- Dosya içeriği güvenlik kontrolü
- .env dosyası oluşturulmalı

### 3. Performans
- Database indexing
- Caching stratejisi
- Pagination optimizasyonu
- Media dosyaları için CDN

### 4. Test Coverage
- Unit testler
- Integration testler
- API endpoint testleri

## Çevre Değişkenleri Konfigürasyonu

### .env Dosyası
Proje kökünde `.env` dosyası mevcut ve aşağıdaki konfigürasyonları içeriyor:

```bash
# PostgreSQL Database Configuration
DB_NAME=gamehost_db
DB_USER=gamehost_user
DB_PASSWORD=kasim123
DB_HOST=localhost
DB_PORT=5432

# Django Secret Key
SECRET_KEY=ek_v^s#nt5t4r3$72fg_6qmlk$w2cp(9yv#i1d1sxt9^&l%iaj%
```

### .gitignore Konfigürasyonu
Proje kapsamlı bir `.gitignore` dosyası ile yapılandırılmış:

**Ignored Categories:**
- ✅ Python cache files (`__pycache__/`, `*.pyc`)
- ✅ Environment files (`.env`, `.venv/`)
- ✅ Django specifics (`*.log`, `db.sqlite3`, `media/`, `static/`)
- ✅ IDE files (`.vscode/`, `.idea/`)
- ✅ OS files (`.DS_Store`, `Thumbs.db`)
- ✅ Package/build files (`dist/`, `build/`, `*.egg-info/`)
- ✅ Test coverage (`htmlcov/`, `.coverage`)
- ✅ Security sensitive files (`*.pem`, `*.key`, `credentials.*`)

**Güvenlik Özellikleri:**
- Media ve static klasörler ignore ediliyor (uploads korunuyor)
- Tüm .env variants ignore ediliyor (`.env.*`)
- Credential dosyaları ignore ediliyor
- IDE ve sistem dosyaları ignore ediliyor

### Güvenlik Notları
- ✅ SECRET_KEY çevre değişkeninden alınıyor
- ✅ Veritabanı bilgileri çevre değişkenlerinde saklanıyor
- ✅ .env dosyası .gitignore'a eklenmiş ve version control'dan hariç tutuluyor
- ✅ Kapsamlı .gitignore konfigürasyonu mevcut
- ⚠️ Production ortamında SECRET_KEY'in değiştirilmesi önerilir
- ⚠️ Production ortamında güçlü veritabanı şifresi kullanılmalı

## API Features (Devam)

### 8. **Advanced Filtering System (Step 17)**
- **Dosya:** `games/filters.py`
- **Özellikler:**
  - Genre/Tag filtering (ID veya slug ile)
  - Search functionality (title, description)
  - Creator filtering
  - Date range filtering
  - Validation ile error handling

### 9. **CORS (Cross-Origin Resource Sharing) Configuration**
- **Dosya:** `gamehost_project/settings.py`, `gamehost_project/middleware.py`
- **Özellikler:**
  - Development/Production ayrımı
  - Güvenli CORS headers
  - Suspicious origin blocking
  - CORS request monitoring
  - Custom security middleware

## Security Features

### 1. **CORS Security**
```python
# Development (gevşek ayarlar)
CORS_ALLOW_ALL_ORIGINS = True  
CORS_ALLOW_CREDENTIALS = True

# Production (sıkı güvenlik)
CORS_ALLOWED_ORIGINS = ["https://yourdomain.com"]
CORS_ALLOW_ALL_ORIGINS = False
```

### 2. **Security Headers**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cache-Control: no-cache` (API endpoints için)

### 3. **Custom Security Middleware**
- **Suspicious Origin Blocking:** `null`, `file:`, `chrome-extension:` 
- **CORS Monitoring:** Tüm cross-origin istekleri loglanır
- **Bot Detection:** Düşük user-agent kontrolü
- **API Versioning:** Response headers'da versiyon bilgisi

## Sonuç

GameHost Platform, Django REST Framework tabanlı sağlam bir backend API'si olarak geliştirilmiş. Temel oyun yükleme, kullanıcı kimlik doğrulama, oylama ve raporlama sistemleri tamamen işlevsel durumda. Moderasyon sistemi ve dosya işleme özellikleri özellikle gelişmiş. 

**Güvenlik konfigürasyonu da iyi durumdadır:**
- ✅ Environment variables düzgün ayarlanmış
- ✅ .env dosyası güvenli şekilde ignore ediliyor
- ✅ Kapsamlı .gitignore konfigürasyonu

Sadece leaderboard sistemi, testing, güvenlik sertleştirme ve deployment konfigürasyonunun tamamlanması ile production-ready hale getirilebilir. 
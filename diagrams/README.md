# Game Hosting Platform - Mimari Diyagramları

Bu klasör, Game Hosting Platform Backend projesi için Mermaid formatında mimari diyagramları içermektedir.

## 📁 Dosya Listesi

### 1. `sistem_mimarisi.mmd`
- **Açıklama**: Ana sistem mimarisi diyagramı
- **Tip**: Mermaid Graph (TB - Top to Bottom)
- **İçerik**: Client Layer, Network Layer, Application Layer, Data Layer
- **Kullanım**: Genel sistem mimarisi sunumları için

### 2. `guvenlik_mimarisi.mmd`
- **Açıklama**: Güvenlik katmanları ve tehdit modeli
- **Tip**: Mermaid Graph (TB - Top to Bottom)
- **İçerik**: External Threats, Security Layers, Protected Resources
- **Kullanım**: Güvenlik dokümantasyonu ve risk analizi için

### 3. `veritabani_mimarisi.mmd`
- **Açıklama**: Veritabanı şeması ve ilişkileri
- **Tip**: Mermaid ERD (Entity Relationship Diagram)
- **İçerik**: Tüm tablolar, ilişkiler, alanlar
- **Kullanım**: Veritabanı tasarım dokümantasyonu için

### 4. `class_diagram.mmd`
- **Açıklama**: Sınıf yapısı ve nesne ilişkileri
- **Tip**: Mermaid Class Diagram
- **İçerik**: Models, Serializers, ViewSets, Services, Middleware
- **Kullanım**: OOP yapısı ve kod mimarisi dokümantasyonu için

## 🛠️ Kullanım Talimatları

### Online Editörler
1. **Mermaid Live Editor**: https://mermaid.live/
2. **Draw.io**: https://app.diagrams.net/ (Mermaid desteği)
3. **GitHub**: Otomatik Mermaid rendering

### Visual Studio Code
```bash
# Mermaid Preview Extension
ext install bierner.markdown-mermaid
```

### Markdown Dosyalarında Kullanım
```markdown
```mermaid
# Dosya içeriğini buraya kopyalayın
```

### HTML/Web Sayfalarında Kullanım
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>

<div class="mermaid">
  <!-- Mermaid kod buraya -->
</div>
```

## 📊 Diyagram Tipleri

### Graph (sistem_mimarisi.mmd, guvenlik_mimarisi.mmd)
- **Format**: `graph TB` (Top to Bottom)
- **Özellikler**: Subgraphs, nodes, connections
- **Kullanım**: Sistem akışları ve bileşen ilişkileri

### ERD (veritabani_mimarisi.mmd)
- **Format**: `erDiagram`
- **Özellikler**: Entities, relationships, attributes
- **Kullanım**: Veritabanı şeması visualizasyonu

### Class Diagram (class_diagram.mmd)
- **Format**: `classDiagram`
- **Özellikler**: Classes, inheritance, composition, methods, attributes
- **Kullanım**: OOP yapısı ve sınıf ilişkileri gösterimi

## 🎨 Styling Önerileri

### Renk Kodları
```css
/* Güvenlik katmanları için */
.security { fill: #ff6b6b; }
.middleware { fill: #4ecdc4; }
.database { fill: #45b7d1; }
.application { fill: #96ceb4; }

/* Class diagram katmanları için */
.model { fill: #ff9f43; }
.serializer { fill: #6c5ce7; }
.viewset { fill: #00b894; }
.service { fill: #fd79a8; }
```

### Mermaid Tema Seçenekleri
```javascript
mermaid.initialize({
  theme: 'default',    // default, dark, forest, neutral
  themeVariables: {
    primaryColor: '#4ecdc4',
    primaryTextColor: '#333'
  }
});
```

## 📋 Güncellenme Geçmişi

### v1.2 (December 30, 2024) - Complete Authentication System
- **JWT Logout System**: Added JWTLogoutAPIView to class diagram
- **Token Blacklisting**: Updated security architecture with token blacklist security layer
- **Password Change System**: Added ChangePasswordAPIView and ChangePasswordSerializer
- **Enhanced Security**: Updated security architecture with password security layer
- **System Architecture**: Added Password Change Service to core services
- **Authentication Flow**: Complete authentication system with logout and password management

- **v1.1 (30 Aralık 2024)**: Class Diagram eklendi
  - Sınıf yapısı ve ilişkileri diyagramı eklendi
  - Models, Serializers, ViewSets, Services gösterimi
  - OOP inheritance ve composition ilişkileri

- **v1.0 (30 Aralık 2024)**: İlk versiyon
  - Sistem mimarisi diyagramı eklendi
  - Güvenlik mimarisi diyagramı eklendi
  - Veritabanı ERD diyagramı eklendi

## 📞 Destek

Bu diyagramlar hakkında sorularınız için:
- Main dokümantasyon: `UYGULAMA_MIMARISI.md`
- Proje dokümantasyonu: `CODEBASE_DOCUMENTATION.md`

---

**Not**: Bu diyagramlar projenin mevcut durumunu yansıtmaktadır. Sistem güncellendiğinde diyagramların da güncellenmesi gerekebilir. 
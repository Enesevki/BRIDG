# games/migrations/XXXX_load_initial_genres_tags.py

from django.db import migrations
from django.utils.text import slugify # slugify'ı import etmeyi unutmayın

# Sabit Genre ve Tag listeleriniz
GENRES_DATA = [
    "Aksiyon", "Macera", "Eğlence", "Simülasyon", "RYO",
    "Strateji", "Spor", "Yarış"
]

TAGS_DATA = [
    "Nişancı", "Sandbox", "Arcade", "Rogue-like", "Bulmaca", "Platform",
    "Yaşam", "Sıra Tabanlı", "Görsel Roman", "Kart Oyunu", "GZS", "Şehir Kurma",
    "Eğitici", "Kule Savunması", "İnteraktif Kurgu", "Point & Click", "Yürüme",
    "İlişki", "E-spor", "Parti Tabanlı", "Koloni", "Masa Oyunları",
    "Kutu Oyunu", "Uzay", "Çiftçilik", "Otomobil", "Beat 'em up", "3D Dövüş",
    "Battle Royale", "Çok Oyunculu", "JRYO", "Yardımcı Uygulamalar", "Ritim",
    "Büyük Strateji", "2D Dövüş", "Auto Battler", "Tasarım ve İllüstrasyon",
    "MOBA", "Animasyon ve Modelleme", "4X", "Kelime Oyunu"
]


def load_genres(apps, schema_editor):
    Genre = apps.get_model('games', 'Genre')
    for genre_name in GENRES_DATA:
        if not genre_name.strip():  # Boş veya sadece boşluk içeren isimleri atla
            print(f"Uyarı: Boş genre adı atlanıyor: '{genre_name}'")
            continue
        
        potential_slug = slugify(genre_name)
        if not potential_slug:  # Eğer slugify sonucu boşsa
            # Bu durumu nasıl ele alacağınıza karar verin:
            # 1. Benzersiz bir slug üretin (örn: genre_name + uuid)
            # 2. Bu kaydı atlayın ve loglayın
            # 3. Hata fırlatın (migration dursun)
            print(f"Uyarı: '{genre_name}' için boş slug üretildi. Bu genre atlanıyor.")
            continue # Şimdilik atlıyoruz

        # get_or_create'i slug'ı da kontrol edecek şekilde kullanalım
        # veya name'i unique kabul edip slug'ı defaults ile set edelim.
        # Modelimizde name unique olduğu için, sadece name ile get_or_create yapmak
        # ve slug'ın modelin save() metodunda oluşmasını beklemek daha mantıklıydı.
        # Ancak boş slug sorununu çözmek için slug'ı burada oluşturup kontrol edelim.
        
        # YÖNTEM 1: Slug'ı defaults ile göndermek (Modelin save() metoduna güvenir)
        # Genre.objects.get_or_create(name=genre_name) # Bu satır hala sorun çıkarıyorsa, aşağıdaki yöntemi deneyin

        # YÖNTEM 2: Slug'ı da get_or_create'e dahil etmek (daha explicit)
        # Bu durumda modelin save() metodundaki slug oluşturma biraz gereksizleşebilir
        # ama zararı olmaz, eğer slug boş gelirse yine oluşturur.
        Genre.objects.get_or_create(
            name=genre_name,
            defaults={'slug': potential_slug} # Eğer obje oluşturulacaksa slug bu olsun
        )


def load_tags(apps, schema_editor):
    Tag = apps.get_model('games', 'Tag')
    for tag_name in TAGS_DATA:
        if not tag_name.strip():
            print(f"Uyarı: Boş tag adı atlanıyor: '{tag_name}'")
            continue
        
        potential_slug = slugify(tag_name)
        if not potential_slug:
            print(f"Uyarı: '{tag_name}' için boş slug üretildi. Bu tag atlanıyor.")
            continue
        
        Tag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': potential_slug}
        )


def delete_genres(apps, schema_editor):
    # Bu migration geri alınırsa (unmigrate) verileri silmek için (isteğe bağlı)
    Genre = apps.get_model('games', 'Genre')
    Genre.objects.filter(name__in=GENRES_DATA).delete()


def delete_tags(apps, schema_editor):
    Tag = apps.get_model('games', 'Tag')
    Tag.objects.filter(name__in=TAGS_DATA).delete()


class Migration(migrations.Migration):

    dependencies = [
        # Bu migration'ın, Genre ve Tag modellerini oluşturan
        # önceki migration'a (genellikle 0001_initial.py) bağlı olduğundan emin olun.
        # Eğer 0001_initial.py dosyanızın adı farklıysa veya birden fazla
        # games migration'ınız varsa, buradaki dependency'yi doğru migration'a ayarlayın.
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_genres, reverse_code=delete_genres),
        migrations.RunPython(load_tags, reverse_code=delete_tags),
    ]

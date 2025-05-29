# backend/games/permissions.py
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission.
    - Read permissions (GET, HEAD, OPTIONS) are allowed if:
        - The object is published, OR
        - The request.user is the owner of the object, OR
        - The request.user is staff/superuser.
    - Write permissions (PUT, PATCH, DELETE) are only allowed to the owner of the object.
    """

    def has_object_permission(self, request, view, obj):
        # obj burada model instance'ıdır (örneğin, Game instance'ı)

        # Okuma izinleri (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            if obj.is_published:  # Modelde 'is_published' alanı olduğunu varsayıyoruz
                return True
            # Yayınlanmamışsa, sadece sahibi veya admin/staff görebilir
            # request.user.is_authenticated kontrolü de eklenebilir ama
            # creator ile karşılaştırma veya is_staff zaten bunu dolaylı olarak sağlar.
            if request.user and request.user.is_authenticated:
                return obj.creator == request.user or request.user.is_staff or request.user.is_superuser
            return False  # Yayınlanmamış ve kullanıcı giriş yapmamışsa göremez

        # Yazma izinleri (PUT, PATCH, DELETE)
        # Sadece objenin sahibi yazma işlemi yapabilir.
        # Adminlerin de yazabilmesini istiyorsak:
        # return obj.creator == request.user or request.user.is_staff or request.user.is_superuser
        # Şimdilik sadece sahibi için bırakalım, adminler için ayrı bir kontrol eklenebilir
        # veya adminler zaten her şeye erişebilir (Django admin paneli gibi).
        # API üzerinden adminlerin her şeyi editlemesi isteniyorsa yukarıdaki yorum satırı açılabilir.
        if request.user and request.user.is_authenticated:
            return obj.creator == request.user  # obj'nin 'creator' alanı olduğunu varsayıyoruz
        return False
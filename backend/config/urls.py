from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "مدیریت سامانه ملی تخصیص کلیه"
admin.site.site_title = "مدیریت Renalloc"
admin.site.index_title = "پنل مدیر سامانه"
admin.site.index_template = "admin/registry_index.html"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/registry/", include("registry.urls")),
]

from django.urls import path, include

from bot_app import admin

urlpatterns = [
    path(r'admin/', admin.admin.site.urls),
    path(r'grappelli/', include('grappelli.urls')),
    path('', include('bot_app.urls'))
]

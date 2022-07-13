from django.urls import path, include

from bot_app import admin

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.admin.site.urls),
    path('', include('bot_app.urls'))
]

from Auth import views
from Bookly.views import *
from BookPanel.views import *



from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/login', admin_login, name='admin-login'),
    path('', views.index, name='home'),
    path('account/', account_view, name='account')
]

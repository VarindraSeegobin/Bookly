from Auth import views
from Bookly.views import *
from BookPanel.views import *



from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('custom-admin/login/', admin_login, name='admin-login'),  # Changed URL
    path('custom-admin/home/', homepage, name='admin-homepage'),
    path('custom-admin/create_book/', create_book, name='create_book'),
    path('custom-admin/update_book/', update_book, name='update_book'),
    path('custom-admin/update_book/<int:book_id>/', update_book, name='update_book'),
    path('custom-admin/delete_book/', delete_book, name='delete_book'),
    path('custom-admin/confirm_order/', confirm_order, name='confirm_order'),
    path('custom-admin/view_books/', view_books, name='view_books'),
    path('custom-admin/view_orders/', view_orders, name='view_orders'),
    path('custom-admin/view_activity_log/', view_activity_log, name='view_activity_log'),
    path('custom-admin/logout', logout_user, name='logout'),
    path('', views.index, name='home'),
    path('search_books/', views.search_books, name='search_books'),
    path('account/', account_view, name='account'),
    path('cart/', cart_view, name='cart'),
    path('add_to_cart/<int:content_type_id>/<int:object_id>/', add_to_cart, name="add_to_cart"),
    path("update_cart_ajax/", update_cart_ajax, name="update_cart_ajax"),
    path('checkout/', checkout, name='checkout'),
]

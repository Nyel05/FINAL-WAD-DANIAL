from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("register/", views.register, name="register"),
    path("product/", views.product, name="product"),
    path("signout/", views.signout, name="signout"),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('search/', views.search, name='search'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('delete-order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('profile/', views.profile, name='profile'),
]
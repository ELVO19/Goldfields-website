"""
URL configuration for hotel project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin_page/', views.admin_page, name='admin_page'),
    path('menu', views.menu, name='menu'),
    path('contact', views.contact, name='contact'),
    path('add/', views.add_dish, name='add_dish'),
    path('update/<int:dish_id>/', views.update_dish, name='update_dish'),
    path('delete/<int:dish_id>/', views.delete_dish, name='delete_dish'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('payment/<int:id>/', views.payment, name='payment'),
    path('reservation/', views.reservation, name='reservation'),
    path('reservation/success/', views.reservation_success, name='reservation_success'),

    path('reservations/', views.admin_reservations, name='admin_reservations'),
    path('reservations/<int:reservation_id>/status/', views.update_reservation_status,
         name='update_reservation_status'),
    path('reports/', views.reports, name='reports'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:dish_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/count/', views.cart_item_count, name='cart_item_count'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('reports/', views.reports , name='reports')


]

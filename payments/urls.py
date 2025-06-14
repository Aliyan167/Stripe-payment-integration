from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]

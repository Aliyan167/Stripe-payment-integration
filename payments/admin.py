from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('email', 'amount', 'stripe_payment_intent', 'created_at')
    search_fields = ('email', 'stripe_payment_intent')
    list_filter = ('created_at',)

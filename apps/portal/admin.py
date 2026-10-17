from django.contrib import admin
from .models import LoanProduct


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ["provider", "name", "country", "currency", "annual_rate", "illustrative", "verified_at"]
    list_filter = ["country", "currency", "illustrative"]

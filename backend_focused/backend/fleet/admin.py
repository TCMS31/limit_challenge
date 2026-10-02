from django.contrib import admin
from unfold.admin import ModelAdmin

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle


@admin.register(Office)
class OfficeAdmin(ModelAdmin):
    list_display = ("name", "city")
    search_fields = ("name", "city")


@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ("vin", "license_plate", "make", "model", "year", "office", "is_active")
    list_filter = ("is_active", "make", "office")
    search_fields = ("vin", "license_plate", "make", "model")


@admin.register(Mechanic)
class MechanicAdmin(ModelAdmin):
    list_display = ("name", "certification_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "certification_number")


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(ModelAdmin):
    list_display = ("vehicle", "mechanic", "maintenance_date", "maintenance_type", "cost")
    list_filter = ("maintenance_type", "maintenance_date")
    search_fields = ("vehicle__vin", "mechanic__name", "notes")

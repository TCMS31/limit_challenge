from django.core.validators import MinValueValidator
from django.db import models


class MaintenanceType(models.TextChoices):
    OIL_CHANGE = "oil_change", "Oil change"
    INSPECTION = "inspection", "Inspection"
    REPAIR = "repair", "Repair"
    TIRES = "tires", "Tires"


class Office(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return f"{self.name}, {self.city}"


class Vehicle(models.Model):
    vin = models.CharField(max_length=17, unique=True)
    license_plate = models.CharField(max_length=20)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        related_name="vehicles",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["vin"]
        constraints = [
            models.UniqueConstraint(
                fields=["license_plate"],
                condition=models.Q(is_active=True),
                name="unique_active_license_plate",
            ),
        ]
        indexes = [
            models.Index(fields=["office", "is_active"], name="vehicle_office_active_idx"),
            models.Index(fields=["make"], name="vehicle_make_idx"),
            models.Index(fields=["model"], name="vehicle_model_idx"),
        ]

    def __str__(self):
        return self.vin


class Mechanic(models.Model):
    name = models.CharField(max_length=255)
    certification_number = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class MaintenanceRecord(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="maintenance_records",
    )
    mechanic = models.ForeignKey(
        Mechanic,
        on_delete=models.PROTECT,
        related_name="maintenance_records",
    )
    maintenance_date = models.DateField()
    maintenance_type = models.CharField(max_length=32, choices=MaintenanceType.choices)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-maintenance_date", "-id"]
        indexes = [
            models.Index(
                fields=["vehicle", "maintenance_date"],
                name="maint_vehicle_date_idx",
            ),
            models.Index(
                fields=["mechanic", "maintenance_date"],
                name="maint_mechanic_date_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cost__gte=0),
                name="maint_cost_gte_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(maintenance_type__in=MaintenanceType.values),
                name="maint_type_valid",
            ),
        ]

    def __str__(self):
        return f"{self.vehicle_id} {self.maintenance_type} {self.maintenance_date}"

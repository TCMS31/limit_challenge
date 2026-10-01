from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle
from fleet.serializers import (
    MaintenanceRecordSerializer,
    MechanicSerializer,
    OfficeSerializer,
    VehicleSerializer,
)


def integrity_error_detail(exc):
    message = str(exc).lower()
    if "unique_active_license_plate" in message or "license_plate" in message:
        return {"license_plate": "An active vehicle with this license plate already exists."}
    if "vin" in message:
        return {"vin": "A vehicle with this VIN already exists."}
    if "certification_number" in message:
        return {
            "certification_number": "A mechanic with this certification number already exists."
        }
    if "maint_cost_gte_zero" in message:
        return {"cost": "Cost cannot be negative."}
    if "maint_type_valid" in message:
        return {"maintenance_type": "Maintenance type is not valid."}
    return {"detail": "This record conflicts with an existing one."}


class IntegrityProtectedMixin:
    def perform_create(self, serializer):
        self._save(serializer)

    def perform_update(self, serializer):
        self._save(serializer)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ValidationError(
                "This record is still referenced and cannot be deleted."
            ) from exc

    def _save(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise ValidationError(integrity_error_detail(exc)) from exc


class OfficeViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer


class VehicleViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = Vehicle.objects.select_related("office")
    serializer_class = VehicleSerializer


class MechanicViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = Mechanic.objects.all()
    serializer_class = MechanicSerializer


class MaintenanceRecordViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = MaintenanceRecord.objects.select_related("vehicle", "mechanic")
    serializer_class = MaintenanceRecordSerializer

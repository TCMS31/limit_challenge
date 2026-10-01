from datetime import date

from django.db import IntegrityError
from django.db.models import Prefetch
from django.db.models.deletion import ProtectedError
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle
from fleet.queries import (
    duplicate_conflicts,
    mechanic_workloads,
    office_summaries,
    search_vehicles,
    vehicles_needing_maintenance,
)
from fleet.serializers import (
    AssignOfficeSerializer,
    MaintenanceDetailSerializer,
    MaintenanceRecordSerializer,
    MechanicSerializer,
    MechanicWorkloadSerializer,
    OfficeSerializer,
    OfficeSummarySerializer,
    VehicleDetailSerializer,
    VehicleMaintenanceStatusSerializer,
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


def parse_bool(value, field):
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValidationError({field: "Use true or false."})


def parse_date(value, field):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError({field: "Use YYYY-MM-DD."}) from exc


def parse_int(value, field):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "Enter a whole number."}) from exc


class OfficeViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer

    @action(detail=False, methods=["get"])
    def summary(self, request):
        serializer = OfficeSummarySerializer(office_summaries(), many=True)
        return Response(serializer.data)


class VehicleViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = Vehicle.objects.select_related("office")
    serializer_class = VehicleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in {"retrieve", "maintenance"}:
            history = MaintenanceRecord.objects.select_related("mechanic").order_by(
                "-maintenance_date",
                "-id",
            )
            queryset = queryset.prefetch_related(
                Prefetch("maintenance_records", queryset=history)
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return VehicleDetailSerializer
        if self.action == "needs_maintenance":
            return VehicleMaintenanceStatusSerializer
        return VehicleSerializer

    @action(detail=False, methods=["get"])
    def search(self, request):
        maintained_after = parse_date(request.query_params.get("maintained_after"), "maintained_after")
        maintained_before = parse_date(
            request.query_params.get("maintained_before"),
            "maintained_before",
        )
        if (
            maintained_after is not None
            and maintained_before is not None
            and maintained_after > maintained_before
        ):
            raise ValidationError(
                {"maintained_before": "This date must be on or after maintained_after."}
            )
        queryset = search_vehicles(
            office_id=parse_int(request.query_params.get("office"), "office"),
            is_active=parse_bool(request.query_params.get("active"), "active"),
            make=request.query_params.get("make", "").strip(),
            model=request.query_params.get("model", "").strip(),
            maintained_after=maintained_after,
            maintained_before=maintained_before,
            certification_number=request.query_params.get("certification_number", "").strip(),
        )
        return self._paginated(queryset)

    @action(detail=True, methods=["get"])
    def maintenance(self, request, pk=None):
        vehicle = self.get_object()
        serializer = MaintenanceDetailSerializer(vehicle.maintenance_records.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        vehicle = self.get_object()
        serializer = AssignOfficeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle.office = serializer.validated_data["office"]
        vehicle.save(update_fields=["office"])
        return Response(VehicleSerializer(vehicle).data)

    @action(detail=False, methods=["get"], url_path="needs-maintenance")
    def needs_maintenance(self, request):
        return self._paginated(vehicles_needing_maintenance())

    @action(detail=False, methods=["get"], url_path="check-duplicate")
    def check_duplicate(self, request):
        vin = request.query_params.get("vin", "").strip()
        license_plate = request.query_params.get("license_plate", "").strip()
        if not vin and not license_plate:
            raise ValidationError("Provide a VIN, a license plate, or both.")
        conflicts = duplicate_conflicts(
            vin=vin,
            license_plate=license_plate,
            exclude_id=parse_int(request.query_params.get("exclude"), "exclude"),
        )
        return Response({"conflicts": conflicts})

    def _paginated(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class MechanicViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = Mechanic.objects.all()
    serializer_class = MechanicSerializer

    @action(detail=False, methods=["get"])
    def workload(self, request):
        serializer = MechanicWorkloadSerializer(mechanic_workloads(), many=True)
        return Response(serializer.data)


class MaintenanceRecordViewSet(IntegrityProtectedMixin, ModelViewSet):
    queryset = MaintenanceRecord.objects.select_related("vehicle", "mechanic")
    serializer_class = MaintenanceRecordSerializer

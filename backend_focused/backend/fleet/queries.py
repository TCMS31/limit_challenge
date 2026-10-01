from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Count,
    DateField,
    DecimalField,
    Exists,
    F,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle


def office_summaries():
    start = timezone.localdate() - timedelta(days=365)
    active_count = (
        Vehicle.objects.filter(office=OuterRef("pk"), is_active=True)
        .order_by()
        .values("office")
        .annotate(total=Count("pk"))
        .values("total")
    )
    year_cost = (
        MaintenanceRecord.objects.filter(
            vehicle__office=OuterRef("pk"),
            maintenance_date__gte=start,
        )
        .order_by()
        .values("vehicle__office")
        .annotate(total=Sum("cost"))
        .values("total")
    )
    latest = (
        MaintenanceRecord.objects.filter(vehicle__office=OuterRef("pk"))
        .order_by()
        .values("vehicle__office")
        .annotate(latest=Max("maintenance_date"))
        .values("latest")
    )
    money = DecimalField(max_digits=14, decimal_places=2)
    return Office.objects.annotate(
        active_vehicle_count=Coalesce(
            Subquery(active_count[:1], output_field=IntegerField()),
            0,
        ),
        maintenance_cost_last_year=Coalesce(
            Subquery(year_cost[:1], output_field=money),
            Decimal("0"),
            output_field=money,
        ),
        last_maintenance=Subquery(latest[:1], output_field=DateField()),
    ).order_by("name", "id")


def search_vehicles(
    *,
    office_id=None,
    is_active=None,
    make=None,
    model=None,
    maintained_after=None,
    maintained_before=None,
    certification_number=None,
):
    queryset = Vehicle.objects.select_related("office")
    if office_id is not None:
        queryset = queryset.filter(office_id=office_id)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    if make:
        queryset = queryset.filter(make__iexact=make)
    if model:
        queryset = queryset.filter(model__iexact=model)

    maintenance = MaintenanceRecord.objects.filter(vehicle=OuterRef("pk"))
    has_maintenance_filter = False
    if maintained_after is not None:
        maintenance = maintenance.filter(maintenance_date__gte=maintained_after)
        has_maintenance_filter = True
    if maintained_before is not None:
        maintenance = maintenance.filter(maintenance_date__lte=maintained_before)
        has_maintenance_filter = True
    if certification_number:
        maintenance = maintenance.filter(
            mechanic__certification_number=certification_number
        )
        has_maintenance_filter = True
    if has_maintenance_filter:
        queryset = queryset.filter(Exists(maintenance))
    return queryset


def vehicles_needing_maintenance():
    cutoff = timezone.localdate() - timedelta(days=365)
    return (
        Vehicle.objects.filter(is_active=True)
        .annotate(last_maintenance=Max("maintenance_records__maintenance_date"))
        .filter(Q(last_maintenance__isnull=True) | Q(last_maintenance__lt=cutoff))
        .select_related("office")
        .order_by(F("last_maintenance").asc(nulls_first=True), "id")
    )


def mechanic_workloads():
    year = timezone.localdate().year
    this_year = Q(maintenance_records__maintenance_date__year=year)
    money = DecimalField(max_digits=14, decimal_places=2)
    return Mechanic.objects.annotate(
        maintenance_count=Count("maintenance_records", filter=this_year),
        maintenance_cost=Coalesce(
            Sum("maintenance_records__cost", filter=this_year),
            Decimal("0"),
            output_field=money,
        ),
    ).order_by("-maintenance_count", "-maintenance_cost", "name")


def duplicate_conflicts(*, vin, license_plate, exclude_id=None):
    vehicles = Vehicle.objects.all()
    if exclude_id is not None:
        vehicles = vehicles.exclude(pk=exclude_id)
    conflicts = []
    if vin and vehicles.filter(vin=vin).exists():
        conflicts.append("vin")
    if license_plate and vehicles.filter(license_plate=license_plate, is_active=True).exists():
        conflicts.append("license_plate")
    return conflicts

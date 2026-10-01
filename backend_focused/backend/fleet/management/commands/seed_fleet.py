from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from fleet.models import MaintenanceRecord, MaintenanceType, Mechanic, Office, Vehicle

MAKES = {
    "Toyota": ["Camry", "Corolla", "RAV4"],
    "Ford": ["F-150", "Escape", "Focus"],
    "Honda": ["Civic", "Accord", "CR-V"],
    "Chevrolet": ["Silverado", "Malibu", "Equinox"],
}


class Command(BaseCommand):
    help = "Load dummy offices, vehicles, mechanics, and maintenance records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing fleet rows before loading.",
        )
        parser.add_argument("--offices", type=int, default=8)
        parser.add_argument("--vehicles", type=int, default=150)
        parser.add_argument("--mechanics", type=int, default=25)
        parser.add_argument(
            "--heavy",
            type=int,
            default=400,
            help="Maintenance rows to attach to one vehicle.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed so repeated runs produce the same names.",
        )

    def handle(self, *args, **options):
        offices_count = options["offices"]
        vehicles_count = options["vehicles"]
        mechanics_count = options["mechanics"]
        heavy_count = options["heavy"]
        if min(offices_count, vehicles_count, mechanics_count, heavy_count) < 1:
            raise CommandError("Counts must be at least 1.")
        if vehicles_count < 5:
            raise CommandError("Create at least 5 vehicles so the sample cases fit.")

        if self._fleet_has_rows() and not options["clear"]:
            raise CommandError("Fleet tables already have rows. Re-run with --clear.")

        faker = Faker()
        faker.seed_instance(options["seed"])
        today = timezone.localdate()

        with transaction.atomic():
            if options["clear"]:
                MaintenanceRecord.objects.all().delete()
                Vehicle.objects.all().delete()
                Mechanic.objects.all().delete()
                Office.objects.all().delete()

            offices = self._create_offices(faker, offices_count)
            mechanics = self._create_mechanics(faker, mechanics_count)
            vehicles = self._create_vehicles(faker, vehicles_count, offices)
            record_count = self._create_maintenance(
                faker, vehicles, mechanics, today, heavy_count
            )

        heavy = vehicles[max(2, vehicles_count // 10)]
        self.stdout.write(
            self.style.SUCCESS(
                "Seeded "
                f"{len(offices)} offices, {len(vehicles)} vehicles, "
                f"{len(mechanics)} mechanics, {record_count} maintenance records."
            )
        )
        self.stdout.write(f"Vehicle with {heavy_count} maintenance records: VIN {heavy.vin}")

    def _fleet_has_rows(self):
        return (
            Office.objects.exists()
            or Vehicle.objects.exists()
            or Mechanic.objects.exists()
            or MaintenanceRecord.objects.exists()
        )

    def _create_offices(self, faker, count):
        offices = [
            Office(name=f"{faker.unique.city()} Fleet", city=faker.city())
            for _ in range(count)
        ]
        return Office.objects.bulk_create(offices)

    def _create_mechanics(self, faker, count):
        mechanics = [
            Mechanic(
                name=faker.name(),
                certification_number=f"ASE-{index + 1:05d}",
                is_active=index > 0,
            )
            for index in range(count)
        ]
        return Mechanic.objects.bulk_create(mechanics)

    def _create_vehicles(self, faker, count, offices):
        inactive_count = max(2, count // 10)
        vehicles = []
        for index in range(count):
            make = faker.random_element(list(MAKES))
            vehicles.append(
                Vehicle(
                    vin=f"1FAKE{index + 1:012d}",
                    license_plate=f"PLT{index + 1:05d}",
                    make=make,
                    model=faker.random_element(MAKES[make]),
                    year=faker.random_int(2008, 2024),
                    office=offices[index % len(offices)],
                    is_active=index >= inactive_count,
                )
            )
        vehicles[0].license_plate = vehicles[inactive_count].license_plate
        return Vehicle.objects.bulk_create(vehicles)

    def _create_maintenance(self, faker, vehicles, mechanics, today, heavy_count):
        inactive_count = max(2, len(vehicles) // 10)
        active_vehicles = vehicles[inactive_count:]
        heavy = active_vehicles[0]
        never_serviced = active_vehicles[1:13]
        overdue = active_vehicles[13:28]
        regular = active_vehicles[28:]
        active_mechanics = [mechanic for mechanic in mechanics if mechanic.is_active] or mechanics
        types = list(MaintenanceType.values)
        records = []

        records.extend(
            self._records_for_vehicle(
                faker,
                heavy,
                active_mechanics,
                types,
                [today - timedelta(days=day) for day in range(heavy_count)],
            )
        )
        for vehicle in overdue:
            last = today - timedelta(days=faker.random_int(400, 900))
            records.extend(
                self._records_for_vehicle(
                    faker,
                    vehicle,
                    active_mechanics,
                    types,
                    [last, last - timedelta(days=30)],
                )
            )
        for vehicle in regular:
            dates = [
                today - timedelta(days=faker.random_int(0, 200 if faker.boolean() else 700))
                for _ in range(faker.random_int(1, 4))
            ]
            records.extend(
                self._records_for_vehicle(faker, vehicle, active_mechanics, types, dates)
            )
        for vehicle in vehicles[:inactive_count]:
            records.extend(
                self._records_for_vehicle(
                    faker,
                    vehicle,
                    active_mechanics,
                    types,
                    [today - timedelta(days=faker.random_int(10, 100))],
                )
            )

        MaintenanceRecord.objects.bulk_create(records, batch_size=1000)
        return len(records)

    def _records_for_vehicle(self, faker, vehicle, mechanics, types, dates):
        return [
            MaintenanceRecord(
                vehicle=vehicle,
                mechanic=faker.random_element(mechanics),
                maintenance_date=maintenance_date,
                maintenance_type=faker.random_element(types),
                cost=Decimal(faker.random_int(2500, 250000)) / Decimal("100"),
                notes=faker.sentence(),
            )
            for maintenance_date in dates
        ]

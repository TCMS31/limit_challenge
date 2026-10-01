from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle


def days_ago(days):
    return timezone.localdate() - timedelta(days=days)


def cost_window_dates():
    today = timezone.localdate()
    window_start = today - timedelta(days=365)
    previous_year = today.replace(year=today.year - 1, month=12, day=31)
    in_window_previous_year = previous_year if previous_year >= window_start else None
    return today, in_window_previous_year, window_start - timedelta(days=1)


class FleetApiTests(APITestCase):
    def setUp(self):
        self.office = Office.objects.create(name="North", city="Austin")
        self.other_office = Office.objects.create(name="South", city="Dallas")
        self.mechanic = Mechanic.objects.create(
            name="Ada",
            certification_number="ASE-00001",
            is_active=True,
        )

    def vehicle(self, **overrides):
        fields = {
            "vin": "1FAKE000000000001",
            "license_plate": "PLT00001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "office": self.office,
            "is_active": True,
        }
        fields.update(overrides)
        return Vehicle.objects.create(**fields)

    def record(self, vehicle, maintenance_date, cost="10.00", mechanic=None):
        return MaintenanceRecord.objects.create(
            vehicle=vehicle,
            mechanic=mechanic or self.mechanic,
            maintenance_date=maintenance_date,
            maintenance_type="repair",
            cost=Decimal(cost),
            notes="",
        )

    def test_duplicate_vin_returns_field_error(self):
        self.vehicle()
        response = self.client.post(
            "/api/vehicles/",
            {
                "vin": "1FAKE000000000001",
                "license_plate": "PLT00002",
                "make": "Ford",
                "model": "Focus",
                "year": 2021,
                "office": self.office.id,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vin", response.data)

    def test_active_license_plate_must_be_unique_and_inactive_may_share_it(self):
        self.vehicle()
        duplicate = {
            "vin": "1FAKE000000000002",
            "license_plate": "PLT00001",
            "make": "Ford",
            "model": "Focus",
            "year": 2021,
            "office": self.office.id,
            "is_active": True,
        }
        active = self.client.post("/api/vehicles/", duplicate, format="json")
        self.assertEqual(active.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("license_plate", active.data)

        duplicate["vin"] = "1FAKE000000000003"
        duplicate["is_active"] = False
        inactive = self.client.post("/api/vehicles/", duplicate, format="json")
        self.assertEqual(inactive.status_code, status.HTTP_201_CREATED)

    def test_assign_changes_only_the_office(self):
        vehicle = self.vehicle()
        response = self.client.post(
            f"/api/vehicles/{vehicle.id}/assign/",
            {"office": self.other_office.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.office_id, self.other_office.id)
        self.assertEqual(vehicle.vin, "1FAKE000000000001")
        self.assertEqual(vehicle.license_plate, "PLT00001")
        self.assertTrue(vehicle.is_active)

    def test_duplicate_check_reports_conflicting_fields(self):
        self.vehicle()
        self.vehicle(vin="1FAKE000000000009", license_plate="SHARED1", is_active=False)

        both = self.client.get(
            "/api/vehicles/check-duplicate/",
            {"vin": "1FAKE000000000001", "license_plate": "PLT00001"},
        )
        self.assertEqual(both.status_code, status.HTTP_200_OK)
        self.assertEqual(both.data["conflicts"], ["vin", "license_plate"])

        inactive_plate = self.client.get(
            "/api/vehicles/check-duplicate/",
            {"license_plate": "SHARED1"},
        )
        self.assertEqual(inactive_plate.data["conflicts"], [])

        clear = self.client.get(
            "/api/vehicles/check-duplicate/",
            {"vin": "1FAKE000000000099", "license_plate": "FREE01"},
        )
        self.assertEqual(clear.data["conflicts"], [])

    def test_needs_maintenance_filters_and_orders_oldest_first(self):
        never = self.vehicle(vin="1FAKE000000000011", license_plate="NEED0001")
        overdue = self.vehicle(vin="1FAKE000000000012", license_plate="NEED0002")
        self.record(overdue, days_ago(400))
        recent = self.vehicle(vin="1FAKE000000000013", license_plate="NEED0003")
        self.record(recent, days_ago(10))
        inactive = self.vehicle(
            vin="1FAKE000000000014",
            license_plate="NEED0004",
            is_active=False,
        )
        self.record(inactive, days_ago(500))

        response = self.client.get("/api/vehicles/needs-maintenance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [never.id, overdue.id])

    def test_workload_counts_only_the_current_year(self):
        vehicle = self.vehicle()
        this_year, previous_year, outside = cost_window_dates()
        self.record(vehicle, this_year, cost="50.00")
        if previous_year is not None:
            self.record(vehicle, previous_year, cost="25.00")
        self.record(vehicle, outside, cost="999.00")

        response = self.client.get("/api/mechanics/workload/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ada = next(row for row in response.data if row["name"] == "Ada")
        self.assertEqual(ada["maintenance_count"], 1)
        self.assertEqual(Decimal(ada["maintenance_cost"]), Decimal("50.00"))

    def test_office_summary_uses_a_rolling_twelve_months(self):
        vehicle = self.vehicle()
        this_year, previous_year, outside = cost_window_dates()
        self.record(vehicle, this_year, cost="50.00")
        if previous_year is not None:
            self.record(vehicle, previous_year, cost="25.00")
        self.record(vehicle, outside, cost="999.00")
        expected = Decimal("75.00") if previous_year is not None else Decimal("50.00")
        Vehicle.objects.create(
            vin="1FAKE000000000021",
            license_plate="INACT01",
            make="Ford",
            model="Focus",
            year=2019,
            office=self.office,
            is_active=False,
        )

        response = self.client.get("/api/offices/summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        north = next(row for row in response.data if row["name"] == "North")
        self.assertEqual(north["active_vehicle_count"], 1)
        self.assertEqual(Decimal(north["maintenance_cost_last_year"]), expected)
        self.assertEqual(north["last_maintenance"], this_year.isoformat())

    def test_search_combines_office_make_and_maintenance_dates(self):
        match = self.vehicle(vin="1FAKE000000000031", license_plate="SRCH001", make="Toyota")
        self.record(match, days_ago(20))
        other_make = self.vehicle(
            vin="1FAKE000000000032",
            license_plate="SRCH002",
            make="Ford",
            model="Focus",
        )
        self.record(other_make, days_ago(20))
        other_office = self.vehicle(
            vin="1FAKE000000000033",
            license_plate="SRCH003",
            office=self.other_office,
        )
        self.record(other_office, days_ago(20))

        response = self.client.get(
            "/api/vehicles/search/",
            {
                "office": self.office.id,
                "make": "toyota",
                "maintained_after": days_ago(30).isoformat(),
                "maintained_before": days_ago(1).isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data["results"]], [match.id])

    def test_invalid_maintenance_cost_returns_a_message(self):
        vehicle = self.vehicle()
        response = self.client.post(
            "/api/maintenance-records/",
            {
                "vehicle": vehicle.id,
                "mechanic": self.mechanic.id,
                "maintenance_date": days_ago(1).isoformat(),
                "maintenance_type": "repair",
                "cost": "-5.00",
                "notes": "",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cost", response.data)

    def test_vehicle_detail_loads_history_without_a_query_per_record(self):
        vehicle = self.vehicle()
        self.record(vehicle, days_ago(1))
        self.record(vehicle, days_ago(5))
        self.record(vehicle, days_ago(9))

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(f"/api/vehicles/{vehicle.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["office"]["name"], "North")
        self.assertEqual(
            [row["maintenance_date"] for row in response.data["maintenance_records"]],
            [days_ago(1).isoformat(), days_ago(5).isoformat(), days_ago(9).isoformat()],
        )
        self.assertEqual(response.data["maintenance_records"][0]["mechanic"]["name"], "Ada")
        self.assertLessEqual(len(captured.captured_queries), 5)

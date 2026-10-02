from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle
from fleet.queries import (
    _month_start,
    active_vehicles_by_office,
    maintenance_cost_by_month,
    office_summaries,
    top_mechanic_workloads,
)


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
        user = get_user_model().objects.create_user(username="tester", password="secret-pass")
        self.client.force_authenticate(user)
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

        partial = self.client.get(
            "/api/vehicles/search/",
            {"office": self.office.id, "make": "toy", "model": "cam"},
        )
        self.assertEqual(partial.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in partial.data["results"]], [match.id])

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


class JwtAuthTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="fleet", password="fleet-demo")
        self.office = Office.objects.create(name="North", city="Austin")

    def test_fleet_api_requires_a_token(self):
        response = self.client.get("/api/offices/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_check_stays_public(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bad_password_is_rejected(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": "fleet", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_token_can_create_a_vehicle(self):
        token = self.client.post(
            "/api/auth/token/",
            {"username": "fleet", "password": "fleet-demo"},
            format="json",
        )
        self.assertEqual(token.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        response = self.client.post(
            "/api/vehicles/",
            {
                "vin": "1FAKE000000000077",
                "license_plate": "JWT0001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "office": self.office.id,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("refresh", token.data)
        self.assertTrue(token.cookies["fleet_refresh"]["httponly"])

    def test_refresh_cookie_issues_a_new_access_token(self):
        login = self.client.post(
            "/api/auth/token/",
            {"username": "fleet", "password": "fleet-demo"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        refreshed = self.client.post("/api/auth/token/refresh/", {}, format="json")
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data)
        self.assertNotIn("refresh", refreshed.data)
        self.assertNotEqual(refreshed.data["access"], login.data["access"])

    def test_logout_blacklists_the_refresh_cookie(self):
        self.client.post(
            "/api/auth/token/",
            {"username": "fleet", "password": "fleet-demo"},
            format="json",
        )
        refresh = self.client.cookies["fleet_refresh"].value
        logout = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)

        self.client.cookies["fleet_refresh"] = refresh
        reused = self.client.post("/api/auth/token/refresh/", {}, format="json")
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardQueryTests(TestCase):
    def setUp(self):
        self.office = Office.objects.create(name="North", city="Austin")
        self.other_office = Office.objects.create(name="South", city="Dallas")
        self.mechanic = Mechanic.objects.create(
            name="Ada",
            certification_number="ASE-00001",
        )
        self.vehicle = Vehicle.objects.create(
            vin="1FAKE000000000001",
            license_plate="PLT00001",
            make="Toyota",
            model="Camry",
            year=2020,
            office=self.office,
            is_active=True,
        )

    def record(self, maintenance_date, cost="10.00", mechanic=None, vehicle=None):
        return MaintenanceRecord.objects.create(
            vehicle=vehicle or self.vehicle,
            mechanic=mechanic or self.mechanic,
            maintenance_date=maintenance_date,
            maintenance_type="repair",
            cost=Decimal(cost),
            notes="",
        )

    def test_month_buckets_stay_dates_when_truncation_returns_a_datetime(self):
        aware = timezone.make_aware(datetime(2026, 3, 1, 0, 0))
        self.assertEqual(_month_start(aware), timezone.localtime(aware).date().replace(day=1))
        self.assertEqual(_month_start(date(2026, 3, 15)), date(2026, 3, 1))

    def test_monthly_cost_matches_the_rolling_office_summary(self):
        today, previous_year, outside = cost_window_dates()
        self.record(today, "50.00")
        if previous_year is not None:
            self.record(previous_year, "25.00")
        self.record(outside, "999.00")

        months = dict(maintenance_cost_by_month())
        self.assertEqual(months[today.replace(day=1)], Decimal("50.00"))
        if previous_year is not None:
            self.assertEqual(months[previous_year.replace(day=1)], Decimal("25.00"))
        self.assertNotIn(Decimal("999.00"), months.values())

        chart_total = sum(months.values(), Decimal("0"))
        office_total = sum(
            (office.maintenance_cost_last_year for office in office_summaries()),
            Decimal("0"),
        )
        self.assertEqual(chart_total, office_total)

    def test_active_vehicle_counts_match_the_office_summary(self):
        Vehicle.objects.create(
            vin="1FAKE000000000002",
            license_plate="PLT00002",
            make="Ford",
            model="Focus",
            year=2019,
            office=self.office,
            is_active=False,
        )
        Vehicle.objects.create(
            vin="1FAKE000000000003",
            license_plate="PLT00003",
            make="Honda",
            model="Civic",
            year=2021,
            office=self.other_office,
            is_active=True,
        )

        chart = {office.id: office.active_count for office in active_vehicles_by_office()}
        summary = {
            office.id: office.active_vehicle_count for office in office_summaries()
        }
        self.assertEqual(chart, summary)
        self.assertEqual(chart[self.office.id], 1)
        self.assertEqual(chart[self.other_office.id], 1)

    def test_workload_chart_keeps_the_busiest_mechanics(self):
        other = Mechanic.objects.create(name="Bea", certification_number="ASE-00002")
        self.record(days_ago(1), cost="10.00")
        self.record(days_ago(2), cost="10.00", mechanic=other)
        self.record(days_ago(3), cost="10.00", mechanic=other)

        rows = list(top_mechanic_workloads(limit=1))
        self.assertEqual([row.name for row in rows], ["Bea"])

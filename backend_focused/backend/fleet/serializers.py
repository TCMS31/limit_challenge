from rest_framework import serializers

from fleet.models import MaintenanceRecord, Mechanic, Office, Vehicle


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ["id", "name", "city"]


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "vin",
            "license_plate",
            "make",
            "model",
            "year",
            "office",
            "is_active",
        ]

    def validate(self, attrs):
        license_plate = attrs.get(
            "license_plate",
            getattr(self.instance, "license_plate", None),
        )
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        if is_active and license_plate:
            conflict = Vehicle.objects.filter(license_plate=license_plate, is_active=True)
            if self.instance is not None:
                conflict = conflict.exclude(pk=self.instance.pk)
            if conflict.exists():
                raise serializers.ValidationError(
                    {
                        "license_plate": (
                            "An active vehicle with this license plate already exists."
                        )
                    }
                )
        return attrs


class MechanicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mechanic
        fields = ["id", "name", "certification_number", "is_active"]


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = [
            "id",
            "vehicle",
            "mechanic",
            "maintenance_date",
            "maintenance_type",
            "cost",
            "notes",
        ]

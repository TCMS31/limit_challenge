from rest_framework.routers import DefaultRouter

from fleet.views import (
    MaintenanceRecordViewSet,
    MechanicViewSet,
    OfficeViewSet,
    VehicleViewSet,
)

router = DefaultRouter()
router.register("offices", OfficeViewSet)
router.register("vehicles", VehicleViewSet)
router.register("mechanics", MechanicViewSet)
router.register("maintenance-records", MaintenanceRecordViewSet)

urlpatterns = router.urls

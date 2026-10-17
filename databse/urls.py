from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, ClusterViewSet, DatabaseInstanceViewSet,
    TCPCheckAPIView,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("clusters", ClusterViewSet, basename="cluster")
router.register("instances", DatabaseInstanceViewSet, basename="instance")

urlpatterns = [
    path("", include(router.urls)),
    path("tcp-check/", TCPCheckAPIView.as_view(), name="tcp-check"),
]
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Department, Cluster, DatabaseInstance
from .serializers import (
    DepartmentSerializer, ClusterSerializer, DatabaseInstanceSerializer,
    TCPCheckSerializer
)
from .utils import check_tcp


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by("id")
    serializer_class = DepartmentSerializer
    permission_classes = []
    search_fields = ["name", "code"]
    ordering_fields = ["id", "name", "code"]


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.select_related("department", "owner").all()
    serializer_class = ClusterSerializer
    filterset_fields = ["cluster_type", "environment", "status", "department"]
    search_fields = ["name", "code", "vip", "domain"]
    ordering_fields = ["id", "name", "environment"]


class DatabaseInstanceViewSet(viewsets.ModelViewSet):
    queryset = (
        DatabaseInstance.objects
        .select_related("department", "cluster")
        .all()
    )
    serializer_class = DatabaseInstanceSerializer
    filterset_fields = ["db_type", "environment", "status", "role", "department", "cluster"]
    search_fields = ["name", "instance_id", "connection_host"]
    ordering_fields = ["id", "name", "online_at"]


    # ------- 单实例 TCP 探测 -------
    @action(detail=True, methods=["post"], url_path="check-tcp")
    def check_tcp_action(self, request, pk=None):
        instance = self.get_object()
        ser = TCPCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        host = ser.validated_data.get("host") or instance.connection_host
        port = ser.validated_data.get("port") or instance.port
        timeout = ser.validated_data.get("timeout", 3.0)

        is_alive = check_tcp(host, port, timeout)
        return Response({
            "instance_id": instance.instance_id,
            "host": host,
            "port": port,
            "is_alive": is_alive,
        })



class TCPCheckAPIView(APIView):
    """
    POST /api/database/tcp-check/
    body: {"host": "10.0.0.1", "port": 3306, "timeout": 3}
    或  {"instance_id": "xxx"} 从库里取 host/port
    """

    def post(self, request):
        instance_id = request.data.get("instance_id")
        if instance_id:
            try:
                inst = DatabaseInstance.objects.get(instance_id=instance_id)
            except DatabaseInstance.DoesNotExist:
                return Response({"detail": "实例不存在"}, status=404)
            host = request.data.get("host") or inst.connection_host
            port = request.data.get("port") or inst.port
            timeout = float(request.data.get("timeout", 3.0))
            is_alive = check_tcp(host, port, timeout)
            return Response({
                "instance_id": inst.instance_id,
                "host": host, "port": port,
                "reachable": is_alive,
            })

        ser = TCPCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        is_alive = check_tcp(
            ser.validated_data["host"],
            ser.validated_data["port"],
            ser.validated_data.get("timeout", 3.0),
        )
        return Response({
            "host": ser.validated_data["host"],
            "port": ser.validated_data["port"],
            "reachable": is_alive,
        })
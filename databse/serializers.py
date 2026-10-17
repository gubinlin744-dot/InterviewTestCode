from rest_framework import serializers
from .models import Department, Cluster, DatabaseInstance


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ["path"]


class ClusterSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    instance_count = serializers.IntegerField(source="instances.count", read_only=True)

    class Meta:
        model = Cluster
        fields = "__all__"


class DatabaseInstanceSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    cluster_name = serializers.CharField(source="cluster.name", read_only=True)
    db_type = serializers.CharField(required=True)

    class Meta:
        model = DatabaseInstance
        fields = "__all__"

    def validate_port(self, value):
        if not (1 <= value <= 65535):
            raise serializers.ValidationError("端口需在 1-65535 之间")
        return value

class TCPCheckSerializer(serializers.Serializer):
    host = serializers.CharField(required=False, allow_blank=True)
    port = serializers.IntegerField(required=False, min_value=1, max_value=65535)
    timeout = serializers.FloatField(required=False, default=3.0, min_value=0.1, max_value=10)
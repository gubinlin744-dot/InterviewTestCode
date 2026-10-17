from django.db import models
from django.utils import timezone
from datetime import timedelta

from databse.crypto import decrypt_password, encrypt_password


# Create your models here.

class BaseModel(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True

class Department(BaseModel):
    code = models.CharField(max_length=10, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    managers = models.ManyToManyField('auth.User', related_name='manage_departments', blank=True, null=True)
    sub_departments_path = models.CharField(max_length=100, null=True, blank=True,
                                            help_text='用于查询某部门以及相关下属部门')
    def __str__(self):
        return self.name

class Cluster(BaseModel):
    code = models.CharField(max_length=10, unique=True)
    cluster_type = models.CharField(max_length=100, help_text="用于保存集群的种类，如mysql、postgresql、redis")
    architecture = models.CharField(max_length=30)
    environment = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL
    )
    domain = models.CharField(max_length=200, blank=True)
    tcp_port = models.PositiveIntegerField(null=True, blank=True)
    version = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default="running")

class DatabaseInstance(BaseModel):
    name = models.CharField(max_length=100)
    instance_id = models.CharField(max_length=100, unique=True)
    db_type = models.CharField(max_length=30)
    passport = models.PositiveIntegerField(null=True, blank=True)
    version = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    port = models.PositiveIntegerField()
    connection_host = models.CharField(max_length=200, blank=True)
    cluster = models.ForeignKey(
        Cluster, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="instances"
    )
    tags = models.ManyToManyField("Tag", blank=True)
    online_at = models.DateTimeField(null=True, blank=True)
    expire_at = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True)


class InstanceAccount(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "正常"
        DISABLED = "disabled", "禁用"
        PENDING = "pending", "待轮换"
        FAILED = "failed", "轮换失败"

    instance = models.ForeignKey(
        "DatabaseInstance", on_delete=models.CASCADE, related_name="accounts"
    )
    username = models.CharField(max_length=100)
    password_encrypted = models.TextField()

    privilege = models.CharField(max_length=50, blank=True)   # admin/rw/ro
    is_privileged = models.BooleanField(default=False)        # 是否有权限改其他用户

    rotate_enabled = models.BooleanField(default=True)
    rotate_interval_hours = models.PositiveIntegerField(default=12)
    last_rotated_at = models.DateTimeField(null=True, blank=True)
    next_rotate_at = models.DateTimeField(null=True, blank=True, db_index=True)
    rotate_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("instance", "username")]
        indexes = [models.Index(fields=["next_rotate_at", "rotate_enabled"])]

    def __str__(self):
        return f"{self.username}@{self.instance.instance_id}"

    @property
    def password(self) -> str:
        return decrypt_password(self.password_encrypted)

    def set_password(self, plain: str) -> None:
        self.password_encrypted = encrypt_password(plain)

    def schedule_next_rotation(self, base=None):
        base = base or timezone.now()
        self.next_rotate_at = base + timedelta(hours=self.rotate_interval_hours)


class PasswordHistory(models.Model):
    account = models.ForeignKey(
        InstanceAccount, on_delete=models.CASCADE, related_name="history"
    )
    password_encrypted = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    operator = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
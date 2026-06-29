"""Default ModelAdmin classes for built-in admin models."""

from fastapi_console.modeladmin import ModelAdmin
from fastapi_console.types import ExtraField
from fastapi_console.widgets.inputs import PasswordWidget


class AdminUserAdmin(ModelAdmin):
    tag = "admin"
    icon = "group"
    verbose_name = "Admin User"
    verbose_name_plural = "Admin Users"
    list_display = ["id", "email", "full_name", "is_superuser", "is_active"]
    search_fields = ["email", "full_name"]
    exclude = ["hashed_password", "password_changed_at"]
    extra_fields = [
        ExtraField(
            name="password",
            label="Password",
            required=False,
            required_on_create=True,
            widget=PasswordWidget(),
        ),
    ]

    def prepare_create_data(self, data, request=None):
        from fastapi_console.auth.backend import pwd_context
        password = data.pop("password", None)
        if password:
            data["hashed_password"] = pwd_context.hash(password)
        else:
            data["hashed_password"] = ""
        return data

    def on_create(self, obj, request=None):
        pass

    def prepare_update_data(self, data, request=None):
        from fastapi_console.auth.backend import pwd_context
        password = data.pop("password", None)
        if password:
            data["hashed_password"] = pwd_context.hash(password)
        data.pop("hashed_password", None)
        return data

    def on_update(self, obj, data, request=None):
        pass


class AdminRoleAdmin(ModelAdmin):
    tag = "admin"
    icon = "shield-check"
    verbose_name = "Admin Role"
    verbose_name_plural = "Admin Roles"
    list_display = ["id", "name", "description"]
    search_fields = ["name"]


class AdminRefreshTokenAdmin(ModelAdmin):
    tag = "admin"
    icon = "key"
    verbose_name = "Refresh Token"
    verbose_name_plural = "Refresh Tokens"
    exclude = ["user"]


class AdminPermissionAdmin(ModelAdmin):
    tag = "admin"
    icon = "lock"
    verbose_name = "Permission"
    verbose_name_plural = "Permissions"
    list_display = ["id", "role", "table_name", "can_view", "can_create", "can_edit", "can_delete"]


class AdminFieldPermissionAdmin(ModelAdmin):
    tag = "admin"
    icon = "lock"
    verbose_name = "Field Permission"
    verbose_name_plural = "Field Permissions"
    list_display = ["id", "role_id", "table_name", "field_name", "can_view", "can_edit"]


class AuditLogAdmin(ModelAdmin):
    tag = "admin"
    icon = "clock"
    verbose_name = "Audit Log"
    verbose_name_plural = "Audit Logs"
    list_display = ["id", "user_email", "action", "model_name", "object_id", "timestamp"]
    search_fields = ["user_email", "model_name"]
    readonly_fields = ["user_id", "user_email", "action", "model_name", "table_name", "object_id", "object_repr", "changes", "full_snapshot", "ip_address", "user_agent", "timestamp"]


class AdminUserTOTPAdmin(ModelAdmin):
    tag = "admin"
    icon = "lock"
    verbose_name = "2FA Token"
    verbose_name_plural = "2FA Tokens"
    list_display = ["id", "user_id", "enabled", "secret_key", "created_at"]
    # exclude = ["secret_key", "backup_codes"]


class AdminLoginAttemptAdmin(ModelAdmin):
    tag = "admin"
    icon = "clock"
    verbose_name = "Login Attempt"
    verbose_name_plural = "Login Attempts"
    list_display = ["id", "email", "ip_address", "success", "timestamp"]
    search_fields = ["email", "ip_address"]

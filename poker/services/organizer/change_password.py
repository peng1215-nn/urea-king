"""Reuses poker/services/admin/change_password — same logic, different module path."""
from poker.services.admin.change_password import (
    get_current_account_service,
    update_nickname_service,
    update_password_service,
)

__all__ = ["get_current_account_service", "update_nickname_service", "update_password_service"]

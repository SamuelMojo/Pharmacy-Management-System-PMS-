from pms.security.permissions import Action
from pms.ui.registry import ScreenSpec


def _audit(ctx):
    from pms.ui.audit.audit_screen import AuditScreen

    return AuditScreen(ctx)


SCREENS = [ScreenSpec("audit", "Audit log", _audit, Action.VIEW_AUDIT_LOG, order=910)]

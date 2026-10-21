"""How screens get into the app's sidebar.

To add a screen (this is all a developer does; nobody edits main_window.py):

1. Write your screen as a QWidget in your own folder, e.g. pms/ui/stock/stock_screen.py.
   If it has a ``refresh()`` method, the app calls it every time the screen is shown.
2. In pms/ui/stock/screens.py list it:

       from pms.security.permissions import Action
       from pms.ui.registry import ScreenSpec

       def _stock(ctx):
           from pms.ui.stock.stock_screen import StockScreen
           return StockScreen(ctx)

       SCREENS = [ScreenSpec("stock", "Stock", _stock, Action.VIEW_STOCK, order=20)]

The sidebar shows the screen only to roles allowed to use ``action``. ``order`` sets the
position (lower is higher up). Screens are built the first time they are opened, and if one
fails to build the rest of the app keeps working.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import Callable

from PySide6.QtWidgets import QWidget

import pms.ui
from pms.model.account.user import User
from pms.security.permissions import Action, can
from pms.security.session import Session

log = logging.getLogger("pms.ui")


@dataclass
class AppContext:
    """What every screen receives: who is logged in, and ways to talk to the main window."""

    session: Session
    open_screen: Callable[[str], None] = lambda key: None
    refresh_notifications: Callable[[], None] = lambda: None

    @property
    def user(self) -> User:
        assert self.session.user is not None, "no user is logged in"
        return self.session.user


@dataclass(frozen=True)
class ScreenSpec:
    key: str
    title: str
    factory: Callable[[AppContext], QWidget]
    action: Action | None = None   # None = every logged-in user
    order: int = 100


def discover() -> list[ScreenSpec]:
    """Import pms/ui/<folder>/screens.py for every folder and collect their SCREENS lists."""
    found: dict[str, ScreenSpec] = {}
    for module in pkgutil.iter_modules(pms.ui.__path__):
        if not module.ispkg:
            continue
        name = f"pms.ui.{module.name}.screens"
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name == name:        # this folder has no screens.py yet: fine
                continue
            log.exception("Could not load %s", name)
            continue
        except Exception:
            log.exception("Could not load %s", name)
            continue
        for spec in getattr(mod, "SCREENS", []):
            if spec.key in found:
                log.error("Two screens use the key '%s'; ignoring the one in %s", spec.key, name)
                continue
            found[spec.key] = spec
    return sorted(found.values(), key=lambda s: (s.order, s.title))


def screens_for(user: User, specs: list[ScreenSpec] | None = None) -> list[ScreenSpec]:
    """The screens this user's role may see."""
    chosen = discover() if specs is None else specs
    return [s for s in chosen if s.action is None or can(user.role, s.action)]

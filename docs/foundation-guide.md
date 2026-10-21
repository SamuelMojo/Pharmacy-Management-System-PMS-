# Foundation guide (for all developers)

The foundation (database, login, roles, audit log, notifications, app shell) is already built. This page shows how to plug your own work into it. You should almost never need to edit the foundation files; if you think you do, ask Samuel first.

## Layers

```
ui  ->  service  ->  dao  ->  PostgreSQL
```

- `pms/ui/<yourfolder>/`: screens only. No SQL, no business rules.
- `pms/service/<yourfolder>/`: business rules, permission checks, audit logging.
- `pms/dao/<yourfolder>/`: SQL only, one function per query. Takes a `conn` argument.
- `pms/model/<yourfolder>/`: plain data classes.

## 1. Add a database table

1. Create `migrations/00N_yourthing.sql` (agree the number in the group chat; two files with the same number are refused).
2. Run `python -m pms.migrate`.
3. Never edit a migration after it has been applied or committed. Add a new numbered file for changes.

## 2. Write a DAO function

```python
# pms/dao/stock/medicine_dao.py
def get_by_id(conn, medicine_id):
    return conn.execute("SELECT * FROM medicines WHERE id = %s", (medicine_id,)).fetchone()
```

Rows come back as dictionaries: `row["name"]`. Always use `%s` placeholders, never f-strings with user input.

## 3. Write a service function (permission + transaction + audit)

```python
from pms.dao import database
from pms.dao.stock import medicine_dao
from pms.security import audit
from pms.security.permissions import Action, require

def change_price(actor, medicine_id, new_price):
    require(actor, Action.MANAGE_STOCK)               # raises a friendly error if not allowed
    with database.transaction() as conn:              # commits at the end, rolls back on error
        old = medicine_dao.get_by_id(conn, medicine_id)
        medicine_dao.update_price(conn, medicine_id, new_price)
        audit.log_action(actor, "medicine.price_change", entity="medicine",
                         entity_id=medicine_id, details=f"{old['price']} -> {new_price}",
                         conn=conn)                   # same transaction as the change
```

Raise `ValidationError`, `NotFoundError` or `ConflictError` (from `pms/errors.py`) for problems the user should be told about. Their message is shown on screen as written. Any other exception shows a generic message.

If you need to record a failed attempt *and* tell the user it failed, do the work inside the `with` block, remember the message, and raise after the block (see `auth_service.login`). Raising inside the block rolls back the audit row too.

## 4. Send a notification

```python
from pms.security import notifications
notifications.notify("Low stock", "Paracetamol is below its reorder level.",
                     role=Role.STOCK_MANAGER, entity="medicine", entity_id=12, conn=conn)
```

`role=` goes to everyone with that role; `user_id=` goes to one person. Each person has their own read state. The bell in the top bar updates every 20 seconds.

## 5. Add a screen

1. Write a `QWidget` in `pms/ui/<yourfolder>/`. It receives `ctx` (`ctx.user` is the logged-in user). If it has a `refresh()` method, it is called every time the screen is opened.
2. Create `pms/ui/<yourfolder>/screens.py`:

```python
from pms.security.permissions import Action
from pms.ui.registry import ScreenSpec

def _stock(ctx):
    from pms.ui.stock.stock_screen import StockScreen
    return StockScreen(ctx)

SCREENS = [ScreenSpec("stock", "Stock", _stock, Action.VIEW_STOCK, order=20)]
```

The sidebar shows it only to roles allowed to use that action. You do not edit `main_window.py`. See `pms/ui/home/` and `pms/ui/account/` for working examples. Use the helpers in `pms/ui/widgets.py` (`PageHeader`, `make_table`, `fill_table`, `show_error`, `confirm`, `AutoRefresh`) so every screen looks and behaves the same.

To show changes made by someone on another computer, add `widgets.AutoRefresh(self, self.refresh, seconds=15)` to your screen.

## 6. Permissions

`pms/security/permissions.py` lists every `Action` and which roles may do it. If you need a new action, add it there and add it to the right roles (a one-line change; mention it in your pull request). The system manager can do everything.

## 7. Tests

- Put tests in `tests/`, named `test_*.py`.
- Use the `db` fixture for a clean test database, `make_user(Role.X)` to create a user, and `admin` for a ready system manager. See `tests/conftest.py`.
- Use `qtbot` (pytest-qt) for screens. Tests run with an invisible Qt, so no windows pop up.
- Run `docker compose up -d` first, otherwise database tests are skipped.

## Rules

- Audit log every critical action: user changes, stock changes, price changes, orders, payments, refunds, prescription verification, restricted-medicine sign-off, complaints.
- No real payments: receipts only.
- Never commit `.env`.

#!/usr/bin/env python
"""Financial transactions management script."""
import sys
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"
NOT_EXISTS_CATEGORY = "NotExistCategory"
CATS_KEY = "cats"
DATE_PARTS_COUNT = 3
CAT_PARTS_COUNT = 2
INCOME_COMMAND_PARTS = 3
COST_COMMAND_PARTS = 4
STATS_COMMAND_PARTS = 2
MONTHS_IN_YEAR = 12
DAYS_MAX = 31
FEB_MONTH = 2
DATE_KEY = "date"
TYPE_KEY = "type"
AMT_KEY = "amount"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("Misc",),
}

financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    """Check if a year is a leap year."""
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def _get_max_days(month: int, year: int) -> int:
    """Internal helper for max days in month."""
    if month in {4, 6, 9, 11}:
        return 30
    if month == FEB_MONTH:
        return 29 if is_leap_year(year) else 28
    return DAYS_MAX


def _is_valid_day_month(day: int, month: int) -> bool:
    """Validate bounds for day and month."""
    return 1 <= month <= MONTHS_IN_YEAR and 1 <= day <= DAYS_MAX


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """Extract and validate date from string."""
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None

    if not all(d_part.isdigit() for d_part in parts):
        return None

    day, month, year = map(int, parts)

    if not _is_valid_day_month(day, month):
        return None

    if day <= _get_max_days(month, year):
        return day, month, year
    return None


def income_handler(amount: float, date_str: str) -> str:
    """Handle income addition."""
    dt_val = extract_date(date_str)
    if dt_val is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    financial_transactions_storage.append({
        "amount": amount,
        "date": dt_val,
        "type": "income",
    })
    return OP_SUCCESS_MSG


def _is_category_valid(category: str) -> bool:
    """Check if category and subcategory exist."""
    parts = category.split("::")
    if len(parts) != CAT_PARTS_COUNT:
        return False
    main_cat, sub_cat = parts
    return sub_cat in EXPENSE_CATEGORIES.get(main_cat, ())


def cost_handler(category: str, amount: float, date_str: str) -> str:
    """Handle cost addition."""
    dt_val = extract_date(date_str)
    valid_cat = _is_category_valid(category)

    if dt_val is None or amount <= 0 or not valid_cat:
        financial_transactions_storage.append({})
        if dt_val is None:
            return INCORRECT_DATE_MSG
        if amount <= 0:
            return NONPOSITIVE_VALUE_MSG
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append({
        "amount": amount,
        "date": dt_val,
        "type": "cost",
        "category": category,
    })
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    """Return all available cost categories."""
    categories: list[str] = [
        f"{main_cat}::{sub}"
        for main_cat, subs in EXPENSE_CATEGORIES.items()
        for sub in subs
    ]
    return "\n".join(categories)


def _apply_tx(
    current_stats: dict[str, Any],
    transaction: dict[str, Any],
    target_date: tuple[int, int, int],
) -> None:
    """Apply single transaction to total stats dictionary."""
    t_date = transaction[DATE_KEY]
    is_after = (t_date[2], t_date[1], t_date[0]) > (
        target_date[2], target_date[1], target_date[0]
    )
    if is_after:
        return
    is_same_month = t_date[1] == target_date[1]
    is_same_year = t_date[2] == target_date[2]
    amount = transaction[AMT_KEY]
    if transaction[TYPE_KEY] == "income":
        current_stats["t_inc"] += amount
        if is_same_month and is_same_year:
            current_stats["m_inc"] += amount
    else:
        current_stats["t_cost"] += amount
        _update_monthly_costs(
            current_stats,
            transaction,
            is_curr=is_same_month and is_same_year,
        )


def _update_monthly_costs(
    stats: dict[str, Any],
    transaction: dict[str, Any],
    *,
    is_curr: bool,
) -> None:
    """Update monthly cost stats (WPS221 fix)."""
    if not is_curr:
        return

    amount = transaction[AMT_KEY]
    stats["m_cost"] += amount
    category = transaction.get("category", "Other::Misc")
    categories_stats = stats[CATS_KEY]
    current_cat_amount = categories_stats.get(category, 0)
    categories_stats[category] = current_cat_amount + amount


def _get_cat_row(idx: int, name: str, stats: dict[str, Any]) -> str:
    """Helper to fix WPS210: separates loop variables from main function."""
    amount = float(stats[CATS_KEY][name])
    val_str = str(int(amount)) if amount.is_integer() else \
        f"{amount:.10f}".rstrip("0").rstrip(".")
    return f"{idx}. {name}: {val_str}"


def _format_stats(date_str: str, stats: dict[str, Any]) -> str:
    """Format the final statistics string."""
    val = stats["t_inc"] - stats["t_cost"]
    res = [
        f"Ваша статистика по состоянию на {date_str}:",
        f"Суммарный капитал: {val:.2f} рублей",
    ]
    val = stats["m_inc"] - stats["m_cost"]
    msg = "прибыль составила" if val >= 0 else "убыток составил"

    res.extend([
        f"В этом месяце {msg} {abs(val):.2f} рублей",  # noqa: RUF001
        f"Доходы: {stats['m_inc']:.2f} рублей",
        f"Расходы: {stats['m_cost']:.2f} рублей",
        "",
        "Детализация (категория: сумма):",
    ])
    for idx, name in enumerate(sorted(stats[CATS_KEY]), 1):
        res.append(_get_cat_row(idx, name, stats))
    return "\n".join(res)


def show_stats(date_str: str) -> str:
    """Show financial statistics for a specific date."""
    target = extract_date(date_str)
    if target is None:
        return INCORRECT_DATE_MSG

    stats: dict[str, Any] = {
        "t_inc": 0, "t_cost": 0, "m_inc": 0, "m_cost": 0, CATS_KEY: {},
    }
    for t_x in financial_transactions_storage:
        if t_x:
            _apply_tx(stats, t_x, target)

    return _format_stats(date_str, stats)


def _is_float(val_str: str) -> bool:
    """Check if string is a valid float/int without try-except."""
    clean = val_str.replace(",", ".").replace("-", "", 1)
    if clean.count(".") > 1:
        return False
    return clean.replace(".", "", 1).isdigit()


def _handle_income_cmd(parts: list[str]) -> None:
    """Income command logic."""
    if len(parts) == INCOME_COMMAND_PARTS and _is_float(parts[1]):
        val = float(parts[1].replace(",", "."))
        print(income_handler(val, parts[2]))
        return
    print(UNKNOWN_COMMAND_MSG)


def _handle_cost_cmd(parts: list[str]) -> None:
    """Cost command logic."""
    if len(parts) == COST_COMMAND_PARTS and _is_float(parts[2]):
        val = float(parts[2].replace(",", "."))
        print(cost_handler(parts[1], val, parts[3]))
        return
    print(UNKNOWN_COMMAND_MSG)


def _handle_stats_cmd(parts: list[str]) -> None:
    """Stats command logic."""
    if len(parts) == STATS_COMMAND_PARTS:
        print(show_stats(parts[1]))
        return
    print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    """Main entry point with low cognitive complexity."""
    handlers = {
        "income": _handle_income_cmd,
        "cost": _handle_cost_cmd,
        "stats": _handle_stats_cmd,
    }

    for line in sys.stdin:
        parts = line.split()
        if not parts:
            continue

        handler = handlers.get(parts[0])
        if handler:
            handler(parts)
        else:
            print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()

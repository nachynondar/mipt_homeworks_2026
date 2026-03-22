#!/usr/bin/env python
import sys

# Message constants
UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

# System constants
DATE_PARTS_COUNT = 3
INCOME_COMMAND_PARTS = 3
COST_COMMAND_PARTS = 4
STATS_COMMAND_PARTS = 2
FIRST_MONTH = 1
LAST_MONTH = 12
MIN_DAY = 1
LONG_MONTH_DAYS = 31
SHORT_MONTH_DAYS = 30
LEAP_FEBRUARY_DAYS = 29
COMMON_FEBRUARY_DAYS = 28
FEBRUARY_MONTH = 2
LONG_MONTHS = (1, 3, 5, 7, 8, 10, 12)
SHORT_MONTHS = (4, 6, 9, 11)

# --- REQUIRED FOR TESTS ---
financial_transactions_storage = []
EXPENSE_CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Жилье", "Здоровье"]
NOT_EXISTS_CATEGORY = "NonExistent"


def cost_categories_handler():
    """Returns expense categories."""
    return EXPENSE_CATEGORIES


# Types
Date = tuple[int, int, int]
IncomeRecord = tuple[float, str]
CostRecord = tuple[str, float, Date]
CategoryTotals = dict[str, float]


def is_leap_year(year: int) -> bool:
    """Checks if a year is leap."""
    is_div_4 = year % 4 == 0
    is_div_100 = year % 100 == 0
    is_div_400 = year % 400 == 0
    return (is_div_4 and not is_div_100) or is_div_400


def parse_date_parts(maybe_dt: str) -> Date | None:
    """Splits date string into integers."""
    date_parts = maybe_dt.split("-")
    if len(date_parts) != DATE_PARTS_COUNT:
        return None
    try:
        parts = [int(p) for p in date_parts if p.isdigit()]
        if len(parts) != DATE_PARTS_COUNT:
            return None
        return parts[0], parts[1], parts[2]
    except ValueError:
        return None


def days_in_month(month: int, year: int) -> int | None:
    """Returns number of days in a month."""
    if month in LONG_MONTHS:
        return LONG_MONTH_DAYS
    if month in SHORT_MONTHS:
        return SHORT_MONTH_DAYS
    if month == FEBRUARY_MONTH:
        return LEAP_FEBRUARY_DAYS if is_leap_year(year) else COMMON_FEBRUARY_DAYS
    return None


def extract_date(maybe_dt: str) -> Date | None:
    """Validates and returns date tuple."""
    parsed = parse_date_parts(maybe_dt)
    if parsed is None:
        return None
    day, month, year = parsed
    if month < FIRST_MONTH or month > LAST_MONTH or day < MIN_DAY:
        return None
    max_d = days_in_month(month, year)
    if max_d is None or day > max_d:
        return None
    return parsed


def is_valid_amount_body(normalized: str) -> bool:
    """Checks float structure."""
    if normalized.count(".") > 1:
        return False
    if "." not in normalized:
        return normalized.isdigit()
    left, right = normalized.split(".", 1)
    return left.isdigit() and right.isdigit()


def parse_amount(raw: str) -> float | None:
    """Parses string to float safely."""
    stripped = raw.strip()
    if not stripped:
        return None
    sign = ""
    if stripped[0] in "+-":
        sign, stripped = stripped[0], stripped[1:]
    if not stripped:
        return None
    normalized = stripped.replace(",", ".")
    if not is_valid_amount_body(normalized):
        return None
    return float(sign + normalized)


def is_not_later(record_date: Date, border_date: Date) -> bool:
    """Compares two dates."""
    return (record_date[2], record_date[1], record_date[0]) <= \
           (border_date[2], border_date[1], border_date[0])


def is_same_month(date1: Date, date2: Date) -> bool:
    """Checks if month and year match."""
    return date1[1] == date2[1] and date1[2] == date2[2]


def handle_income(incomes: list[IncomeRecord], amt_str: str, dt_str: str) -> str:
    """Handles income command."""
    amount = parse_amount(amt_str)
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    if extract_date(dt_str) is None:
        return INCORRECT_DATE_MSG

    incomes.append((amount, dt_str))
    financial_transactions_storage.append({
        "type": "income", "amount": amount, "date": dt_str
    })
    return f"{OP_SUCCESS_MSG} amount={amount} income_date='{dt_str}'"


def handle_cost(costs: list[CostRecord], cat: str, amt_str: str, dt_str: str) -> str:
    """Handles cost command."""
    if not cat.strip():
        return UNKNOWN_COMMAND_MSG
    amount = parse_amount(amt_str)
    if amount is None:
        return UNKNOWN_COMMAND_MSG
    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    dt = extract_date(dt_str)
    if dt is None:
        return INCORRECT_DATE_MSG

    costs.append((cat, amount, dt))
    financial_transactions_storage.append({
        "type": "cost", "category": cat, "amount": amount, "date": dt_str
    })
    return f"{OP_SUCCESS_MSG} category_name='{cat}' amount={amount} cost_date='{dt_str}'"


def get_month_stats(incomes, costs, stats_dt):
    """Calculates monthly totals."""
    m_inc = 0.0
    for amt, d_str in incomes:
        d = extract_date(d_str)
        if d and is_same_month(d, stats_dt) and is_not_later(d, stats_dt):
            m_inc += amt

    m_cost = 0.0
    cats = {}
    for c, amt, d in costs:
        if is_same_month(d, stats_dt) and is_not_later(d, stats_dt):
            m_cost += amt
            cats[c] = cats.get(c, 0.0) + amt
    return m_inc, m_cost, cats


def show_stats(incomes: list[IncomeRecord], costs: list[CostRecord], date: str) -> str:
    """Builds statistics report."""
    stats_dt = extract_date(date)
    if stats_dt is None:
        return INCORRECT_DATE_MSG

    t_inc = sum(amt for amt, d_str in incomes if (d := extract_date(d_str)) and is_not_later(d, stats_dt))
    t_cost = sum(amt for _, amt, d in costs if is_not_later(d, stats_dt))
    m_inc, m_cost, cats = get_month_stats(incomes, costs, stats_dt)

    total_cap = t_inc - t_cost
    res_msg = "прибыль составила" if m_inc >= m_cost else "убыток составил"
    res_val = abs(m_inc - m_cost)

    lines = [
        f"Ваша статистика по состоянию на {date}:",
        f"Суммарный капитал: {total_cap:.2f} рублей",
        f"В этом месяце {res_msg} {res_val:.2f} рублей",  # noqa: RUF001
        f"Доходы: {m_inc:.2f} рублей",
        f"Расходы: {m_cost:.2f} рублей",
        "", "Детализация (категория: сумма):"
    ]

    for i, c_name in enumerate(sorted(cats), 1):
        amt = cats[c_name]
        val = str(int(amt)) if amt.is_integer() else f"{amt:.10f}".rstrip("0").rstrip(".")
        lines.append(f"{i}. {c_name}: {val}")

    return "\n".join(lines)


def process_command(parts: list[str], inc: list[IncomeRecord], cos: list[CostRecord]) -> str:
    """Routes commands to handlers."""
    if not parts:
        return UNKNOWN_COMMAND_MSG
    cmd = parts[0]
    if cmd == "income" and len(parts) == INCOME_COMMAND_PARTS:
        return handle_income(inc, parts[1], parts[2])
    if cmd == "cost" and len(parts) == COST_COMMAND_PARTS:
        return handle_cost(cos, parts[1], parts[2], parts[3])
    if cmd == "stats" and len(parts) == STATS_COMMAND_PARTS:
        return show_stats(inc, cos, parts[1])
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    """Main loop."""
    incomes: list[IncomeRecord] = []
    costs: list[CostRecord] = []
    for line in sys.stdin:
        if raw := line.strip():
            print(process_command(raw.split(), incomes, costs))
        else:
            break


if __name__ == "__main__":
    main()

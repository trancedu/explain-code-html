"""Normalize, deduplicate, categorize and summarize sample USD expenses."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json


@dataclass(frozen=True)
class Expense:
    day: str
    merchant: str
    cents: int
    category: str


RULES = (
    ("groceries", ("costco", "trader joe", "whole foods")),
    ("transport", ("nj transit", "uber", "parking")),
    ("dining", ("cafe", "restaurant")),
)


def parse_cents(value: str) -> int:
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError("invalid amount") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be finite and positive")
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded == 0:
        raise ValueError("amount rounds to zero")
    return int(rounded * 100)


def categorize(merchant: str) -> str:
    lowered = merchant.casefold()
    for category, keywords in RULES:
        if any(word in lowered for word in keywords):
            return category
    return "other"


def normalize(row: dict) -> Expense:
    day = date.fromisoformat(row["date"]).isoformat()
    merchant = " ".join(row["merchant"].split())
    if not merchant:
        raise ValueError("merchant is empty")
    return Expense(
        day=day,
        merchant=merchant,
        cents=parse_cents(row["amount"]),
        category=categorize(merchant),
    )


def process(rows: list[dict]) -> dict:
    seen = set()
    expenses = []
    rejected = []
    duplicates = 0
    for index, row in enumerate(rows, start=1):
        try:
            expense = normalize(row)
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            rejected.append({"row": index, "reason": str(exc)})
            continue
        key = (expense.day, expense.merchant.casefold(), expense.cents)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        expenses.append(expense)
    totals = {}
    for expense in expenses:
        previous = totals.get(expense.category, 0)
        totals[expense.category] = previous + expense.cents
    return {
        "accepted": len(expenses),
        "duplicates": duplicates,
        "rejected": rejected,
        "totals_cents": dict(sorted(totals.items())),
        "grand_total_cents": sum(totals.values()),
    }


SAMPLE = [
    {"date": "2026-10-16", "merchant": " Costco ", "amount": "$25.105"},
    {"date": "2026-10-16", "merchant": "COSTCO", "amount": "25.11"},
    {"date": "2026-10-16", "merchant": "NJ Transit", "amount": "5.50"},
    {"date": "2026-10-16", "merchant": "Local Cafe", "amount": "8.40"},
    {"date": "2026-10-16", "merchant": "Bookshop", "amount": "12.00"},
    {"date": "2026-10-16", "merchant": "Unknown", "amount": "NaN"},
]


if __name__ == "__main__":
    print(json.dumps(process(SAMPLE), indent=2, ensure_ascii=False))

"""Offline statement reconciliation retained for the branch-office export format."""

from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json


DEFAULT_OPTIONS = {
    "currency": "USD",
    "tolerance": "0.01",
    "date_window": 2,
    "allow_reference_fallback": True,
    "allow_grouped_deposits": True,
    "ignore_pending": True,
    "strict_currency": False,
    "include_rows": True,
    "stop_on_bad_row": False,
    "closing_balance": None,
    "opening_balance": "0.00",
}


def reconcile_statement(statement, ledger, options=None):
    """Return a JSON-friendly report; input row dictionaries are not modified."""
    settings = dict(DEFAULT_OPTIONS)
    if options:
        settings.update(options)
    report = {
        "status": "building",
        "currency": settings["currency"],
        "matches": [],
        "unmatched_statement": [],
        "unmatched_ledger": [],
        "ignored": [],
        "errors": [],
        "warnings": [],
        "totals": {},
    }
    try:
        tolerance = money(settings["tolerance"])
        opening = money(settings["opening_balance"])
        window = int(settings["date_window"])
        if tolerance < 0 or window < 0 or window > 31:
            raise ValueError("Tolerance or date window is outside the supported range")
    except (ValueError, InvalidOperation, TypeError) as exc:
        report["status"] = "rejected"
        report["errors"].append({"scope": "options", "message": str(exc)})
        return report
    if not isinstance(statement, list) or not isinstance(ledger, list):
        report["status"] = "rejected"
        report["errors"].append({"scope": "input", "message": "Both inputs must be lists"})
        return report
    prepared = {"statement": [], "ledger": []}
    seen = {"statement": set(), "ledger": set()}
    statement_total = Decimal("0.00")
    ledger_total = Decimal("0.00")
    for side, rows in (("statement", statement), ("ledger", ledger)):
        for index, raw in enumerate(rows):
            row_id = str(raw.get("id", "")) if isinstance(raw, dict) else ""
            if not row_id:
                row_id = side[0].upper() + str(index + 1)
            if not isinstance(raw, dict):
                report["errors"].append({"scope": side, "id": row_id, "message": "Row must be an object"})
                if settings["stop_on_bad_row"]:
                    report["status"] = "rejected"
                    return report
                continue
            if row_id in seen[side]:
                report["errors"].append({"scope": side, "id": row_id, "message": "Duplicate row id"})
                if settings["stop_on_bad_row"]:
                    report["status"] = "rejected"
                    return report
                continue
            seen[side].add(row_id)
            if settings["ignore_pending"] and raw.get("status", "posted").lower() == "pending":
                report["ignored"].append({"scope": side, "id": row_id, "reason": "pending"})
                continue
            currency = str(raw.get("currency", settings["currency"])).upper()
            if currency != str(settings["currency"]).upper():
                if settings["strict_currency"]:
                    report["errors"].append({"scope": side, "id": row_id, "message": "Foreign currency"})
                    if settings["stop_on_bad_row"]:
                        report["status"] = "rejected"
                        return report
                else:
                    report["ignored"].append({"scope": side, "id": row_id, "reason": "foreign currency"})
                continue
            try:
                amount = signed_amount(raw)
                posted = parse_date(raw["date"])
                reference = normalize_reference(raw.get("reference", ""))
                description = str(raw.get("description", "")).strip()
            except (ValueError, InvalidOperation, KeyError, TypeError) as exc:
                report["errors"].append({"scope": side, "id": row_id, "message": str(exc)})
                if settings["stop_on_bad_row"]:
                    report["status"] = "rejected"
                    return report
                continue
            item = {
                "id": row_id,
                "amount": amount,
                "date": posted,
                "reference": reference,
                "description": description,
                "batch": str(raw.get("batch", "")).strip(),
                "used": False,
                "position": index,
            }
            prepared[side].append(item)
            if side == "statement":
                statement_total += amount
            else:
                ledger_total += amount
    ledger_by_reference = {}
    for item in prepared["ledger"]:
        if item["reference"]:
            ledger_by_reference.setdefault(item["reference"], []).append(item)
    for bank in prepared["statement"]:
        candidates = []
        match_kind = "reference"
        if bank["reference"]:
            for book in ledger_by_reference.get(bank["reference"], []):
                if not book["used"]:
                    day_gap = abs((bank["date"] - book["date"]).days)
                    difference = abs(bank["amount"] - book["amount"])
                    if day_gap <= window and difference <= tolerance:
                        candidates.append((difference, day_gap, book["position"], book))
        if not candidates and settings["allow_reference_fallback"]:
            match_kind = "amount-date"
            for book in prepared["ledger"]:
                if book["used"]:
                    continue
                if bank["reference"] and book["reference"] and bank["reference"] != book["reference"]:
                    continue
                day_gap = abs((bank["date"] - book["date"]).days)
                difference = abs(bank["amount"] - book["amount"])
                if day_gap <= window and difference <= tolerance:
                    candidates.append((difference, day_gap, book["position"], book))
        if candidates:
            candidates.sort(key=lambda entry: entry[:3])
            selected = candidates[0][3]
            if len(candidates) > 1 and candidates[0][:2] == candidates[1][:2]:
                report["warnings"].append("Ambiguous match for " + bank["id"] + "; ledger order won")
            bank["used"] = True
            selected["used"] = True
            report["matches"].append({
                "statement_ids": [bank["id"]],
                "ledger_ids": [selected["id"]],
                "kind": match_kind,
                "statement_amount": display_money(bank["amount"]),
                "ledger_amount": display_money(selected["amount"]),
                "difference": display_money(bank["amount"] - selected["amount"]),
            })
            continue
        if settings["allow_grouped_deposits"] and bank["amount"] > 0 and bank["batch"]:
            group = []
            for book in prepared["ledger"]:
                if not book["used"] and book["batch"] == bank["batch"] and book["amount"] > 0:
                    if abs((bank["date"] - book["date"]).days) <= window:
                        group.append(book)
            group_total = sum((book["amount"] for book in group), Decimal("0.00"))
            if len(group) > 1 and abs(bank["amount"] - group_total) <= tolerance:
                bank["used"] = True
                for book in group:
                    book["used"] = True
                report["matches"].append({
                    "statement_ids": [bank["id"]],
                    "ledger_ids": [book["id"] for book in group],
                    "kind": "deposit-batch",
                    "statement_amount": display_money(bank["amount"]),
                    "ledger_amount": display_money(group_total),
                    "difference": display_money(bank["amount"] - group_total),
                })
                continue
            elif group:
                report["warnings"].append("Batch " + bank["batch"] + " did not balance as a whole")
        report["unmatched_statement"].append(public_row(bank))
    for book in prepared["ledger"]:
        if not book["used"]:
            report["unmatched_ledger"].append(public_row(book))
    difference_total = statement_total - ledger_total
    expected_close = opening + statement_total
    report["totals"] = {
        "opening": display_money(opening),
        "statement_movement": display_money(statement_total),
        "ledger_movement": display_money(ledger_total),
        "movement_difference": display_money(difference_total),
        "expected_closing": display_money(expected_close),
        "matched_groups": len(report["matches"]),
        "accepted_statement_rows": len(prepared["statement"]),
        "accepted_ledger_rows": len(prepared["ledger"]),
    }
    if settings["closing_balance"] is not None:
        try:
            closing = money(settings["closing_balance"])
            closing_gap = closing - expected_close
            report["totals"]["reported_closing"] = display_money(closing)
            report["totals"]["closing_difference"] = display_money(closing_gap)
            if abs(closing_gap) > tolerance:
                report["warnings"].append("Statement closing balance does not match accepted movement")
        except (ValueError, InvalidOperation, TypeError) as exc:
            report["errors"].append({"scope": "closing_balance", "message": str(exc)})
    if report["errors"]:
        report["status"] = "partial"
    elif report["unmatched_statement"] or report["unmatched_ledger"]:
        report["status"] = "review"
    elif abs(difference_total) > tolerance:
        report["status"] = "review"
    elif report["warnings"]:
        report["status"] = "review"
    else:
        report["status"] = "balanced"
    report["reason_counts"] = dict(Counter(row["reason"] for row in report["ignored"]))
    report["review_queue"] = build_review_queue(report)
    if not settings["include_rows"]:
        report["unmatched_counts"] = {
            "statement": len(report["unmatched_statement"]),
            "ledger": len(report["unmatched_ledger"]),
        }
        del report["unmatched_statement"]
        del report["unmatched_ledger"]
    return report


def money(value):
    """Interpret the two amount notations used by the old CSV importer."""
    if isinstance(value, bool):
        raise ValueError("Boolean is not an amount")
    text = str(value).strip().replace(",", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    amount = Decimal(text)
    if not amount.is_finite():
        raise ValueError("Amount must be finite")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def signed_amount(row):
    if "amount" in row and row["amount"] not in (None, ""):
        amount = money(row["amount"])
        direction = str(row.get("direction", "signed")).lower()
        if direction == "debit":
            return -abs(amount)
        if direction == "credit":
            return abs(amount)
        if direction != "signed":
            raise ValueError("Unknown direction: " + direction)
        return amount
    debit = money(row.get("debit") or "0")
    credit = money(row.get("credit") or "0")
    if debit < 0 or credit < 0:
        raise ValueError("Split debit and credit must be nonnegative")
    if debit and credit:
        raise ValueError("A row cannot contain both debit and credit")
    return credit - debit


def parse_date(value):
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if "/" in text:
        month, day, year = (int(part) for part in text.split("/"))
        if year < 100:
            year += 2000 if year < 70 else 1900
        return date(year, month, day)
    return date.fromisoformat(text)


def normalize_reference(value):
    text = str(value).upper().strip()
    if text.startswith("REF:"):
        text = text[4:]
    return "".join(character for character in text if character.isalnum())


def display_money(value):
    return format(value, ".2f")


def public_row(item):
    return {
        "id": item["id"],
        "date": item["date"].isoformat(),
        "amount": display_money(item["amount"]),
        "reference": item["reference"],
        "description": item["description"],
    }


def build_review_queue(report):
    """Keep the old review priority convention for the printed handoff."""
    queue = []
    for side in ("statement", "ledger"):
        for row in report["unmatched_" + side]:
            amount = money(row["amount"])
            if side == "statement":
                if amount < 0:
                    priority = "check-expense"
                else:
                    priority = "check-receipt"
            elif amount < 0:
                priority = "await-withdrawal"
            else:
                priority = "await-deposit"
            queue.append({
                "scope": side,
                "id": row["id"],
                "action": priority,
                "absolute_amount": display_money(abs(amount)),
            })
    queue.sort(key=lambda item: (-money(item["absolute_amount"]), item["scope"], item["id"]))
    return queue


def sample_data():
    statement = [
        {"id": "S1", "date": "2025-03-03", "amount": "(125.00)", "reference": "REF: INV-41"},
        {"id": "S2", "date": "03/04/25", "amount": "300.00", "batch": "DEP-7", "description": "Counter deposit"},
        {"id": "S3", "date": "2025-03-05", "debit": "12.50", "description": "Account service fee"},
        {"id": "S4", "date": "2025-03-06", "amount": "99.00", "status": "pending"},
        {"id": "S5", "date": "2025-03-06", "amount": "20.00", "currency": "EUR"},
    ]
    ledger = [
        {"id": "L1", "date": "2025-03-02", "amount": "125", "direction": "debit", "reference": "inv 41"},
        {"id": "L2", "date": "2025-03-04", "credit": "100", "batch": "DEP-7"},
        {"id": "L3", "date": "2025-03-03", "credit": "200", "batch": "DEP-7"},
        {"id": "L4", "date": "2025-03-05", "amount": "-12.50", "description": "Bank fee"},
    ]
    return statement, ledger


def print_report(report):
    print("Reconciliation:", report["status"])
    if report["totals"]:
        print("Accepted movement:", report["totals"]["statement_movement"], report["currency"])
        print("Movement difference:", report["totals"]["movement_difference"])
    for match in report["matches"]:
        print("Matched", ",".join(match["statement_ids"]), "to", ",".join(match["ledger_ids"]), "via", match["kind"])
    for error in report["errors"]:
        print("Error:", error["scope"], error["message"])
    for warning in report["warnings"]:
        print("Warning:", warning)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    bank_rows, book_rows = sample_data()
    result = reconcile_statement(bank_rows, book_rows, {"opening_balance": "1000", "closing_balance": "1162.50"})
    print_report(result)

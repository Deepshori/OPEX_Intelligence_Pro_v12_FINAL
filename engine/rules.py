import json
import re
from pathlib import Path
from .utils import clean

DEFAULT_CATEGORY_NAMES = {
    "B": "REPAIRS AND MAINTENANCE",
    "C": "SPARES",
    "D": "STORES AND SUPPLIES",
    "E": "LUBRICATING OIL",
    "F": "SERVICES",
    "G": "INSURANCE",
    "H": "MANAGEMENT FEE",
}


def load_json(path, default):
    try:
        if path and Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def load_rules(base_dir=None):
    base = Path(base_dir or Path(__file__).resolve().parents[1])
    default = {
        "exclude_categories": ["A"],
        "included_bill_types": ["Bill", "Bill Credit"],
        "included_journal_categories": ["E"],
        "journal_exclude_ae_journal": ["Accrual", "Reversal"],
        "lo_po_ignore_accounts": ["E1940", "E1941", "E1944"],
        "category_names": DEFAULT_CATEGORY_NAMES,
        "top_items_per_category": 5,
    }
    return load_json(base / "config" / "rules.json", default)


def load_settings(base_dir=None):
    base = Path(base_dir or Path(__file__).resolve().parents[1])
    default = {
        "materiality_usd": 2000,
        "traffic_green_pct": 95,
        "traffic_yellow_pct": 105,
        "large_invoice_usd": 20000,
        "ube_threshold_usd": 5000,
        "old_accrual_days": 60,
        "developer": "Deepak Shori",
        "version": "12.1 Core Engine",
    }
    return load_json(base / "config" / "settings.json", default)


def code_group(code):
    code = clean(code).upper()
    if not code:
        return "Unmapped"
    first = code[0]
    if re.match(r"[A-Z]", first):
        return first
    return "Unmapped"


def category_label(group, rules=None):
    rules = rules or load_rules()
    group = clean(group).upper()
    names = rules.get("category_names", DEFAULT_CATEGORY_NAMES)
    if group in names:
        return f"{group} - {names[group]}"
    if group == "A":
        return "A - EXCLUDED"
    return group or "Unmapped"


def category_sort_key(label_or_group):
    text = clean(label_or_group).upper()
    if text.startswith("UNMAPPED"):
        return "ZZZ"
    return text[:1] if text else "ZZZ"


def is_report_category(label_or_group):
    text = clean(label_or_group).upper()
    return bool(re.match(r"^[B-Z]", text))


def is_excluded_category(group, rules):
    return clean(group).upper() in {clean(x).upper() for x in rules.get("exclude_categories", [])}


def is_bill_type(type_value, rules):
    return clean(type_value).upper() in {clean(x).upper() for x in rules.get("included_bill_types", [])}


def ignore_po_cost_for_account(code, rules):
    return clean(code).upper() in {clean(x).upper() for x in rules.get("lo_po_ignore_accounts", [])}


def include_journal_as_expense(group, type_value, ae_journal, rules):
    included_cats = {clean(x).upper() for x in rules.get("included_journal_categories", [])}
    excluded_ae = {clean(x).upper() for x in rules.get("journal_exclude_ae_journal", [])}
    return clean(group).upper() in included_cats and clean(type_value).upper() == "JOURNAL" and clean(ae_journal).upper() not in excluded_ae

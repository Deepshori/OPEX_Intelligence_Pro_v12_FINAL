import re
import os

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None


def clean(value) -> str:
    if pd is not None:
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
    if value is None:
        return ""
    return str(value).strip()


def norm(value) -> str:
    return re.sub(r"\s+", " ", clean(value).upper())


def amt(value) -> float:
    try:
        if pd is not None and pd.isna(value):
            return 0.0
        text = str(value).replace(",", "").strip()
        if text in ("", "-"):
            return 0.0
        if text.startswith("(") and text.endswith(")"):
            return -float(text[1:-1])
        return float(text)
    except Exception:
        return 0.0


def normalize_key(value) -> str:
    return re.sub(r"[^A-Z0-9]", "", norm(value))


def file_stem_candidates(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"\(\d+\)$", "", stem).strip()
    candidates = [stem]
    parts = re.split(r"[\s_\-]+", stem)
    if parts and parts[0]:
        candidates.append(parts[0])
    cleaned = re.sub(
        r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|JUNE|JULY|YTD|OPEX|EXPENSES|REPORT)\b",
        "",
        stem,
        flags=re.I,
    ).strip()
    if cleaned:
        candidates.append(cleaned)
    out = []
    for c in candidates:
        if c and c not in out:
            out.append(c)
    return out

import pandas as pd
from .utils import clean, amt, normalize_key, file_stem_candidates


def read_master(master_path):
    return pd.read_excel(master_path, header=None)


def get_master_vessels(master_path):
    master = read_master(master_path)
    if master.empty:
        return []
    header = [clean(v) for v in master.iloc[0].tolist()]
    return [v for v in header[2:] if v]


def detect_vessel(master_path, expense_path):
    vessels = get_master_vessels(master_path)
    if not vessels:
        return ""
    lookup = {normalize_key(v): v for v in vessels}
    for cand in file_stem_candidates(expense_path):
        key = normalize_key(cand)
        if key in lookup:
            return lookup[key]
    for cand in file_stem_candidates(expense_path):
        key = normalize_key(cand)
        for vk, vv in lookup.items():
            if key and (key in vk or vk in key):
                return vv
    return ""


def load_budget(master_path, vessel):
    master = read_master(master_path)
    header_row = master.iloc[0].tolist()
    vessel_cols = [i for i, v in enumerate(header_row) if normalize_key(v) == normalize_key(vessel)]
    if not vessel_cols:
        available = ", ".join(get_master_vessels(master_path)[:80])
        raise ValueError(f"Vessel code '{vessel}' not found in Master file header row. Available vessels: {available}")
    vessel_col = vessel_cols[0]
    budget = {}
    descr = {}
    for _, row in master.iloc[1:].iterrows():
        code = clean(row.iloc[0])
        if not code:
            continue
        budget[code] = amt(row.iloc[vessel_col])
        descr[code] = clean(row.iloc[1]) if len(row) > 1 else ""
    return budget, descr

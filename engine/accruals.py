from collections import defaultdict
from .utils import clean, norm, amt
from .rules import code_group, is_excluded_category


def build_open_accruals(mrx, account_name, descr, rules):
    accrual_net = defaultdict(float)
    accrual_rows = defaultdict(list)
    required = ["Owners Code", "AE Journal", "AE Reference PO#", "Description", "Amount (USD)"]
    for c in required:
        if c not in mrx.columns:
            return defaultdict(float), []
    for _, row in mrx.iterrows():
        code = clean(row["Owners Code"])
        if not code:
            continue
        group = code_group(code)
        if is_excluded_category(group, rules):
            continue
        ae = norm(row["AE Journal"])
        if ae in ("ACCRUAL", "REVERSAL"):
            po = norm(row["AE Reference PO#"])
            desc = norm(row["Description"])
            key_ref = po if po else desc
            key = (code, key_ref)
            accrual_net[key] += amt(row["Amount (USD)"])
            accrual_rows[key].append(row)
    open_by_code = defaultdict(float)
    details = []
    for (code, key_ref), net in accrual_net.items():
        if abs(net) <= 0.005:
            continue
        open_by_code[code] += net
        sample = accrual_rows[(code, key_ref)][0]
        details.append({
            "Account Code": code,
            "Account Name/Description": descr.get(code, account_name.get(code, "")),
            "Match Key (PO or Description)": key_ref,
            "Sample Description": clean(sample["Description"]),
            "Open Amount": net,
            "Lines Matched": len(accrual_rows[(code, key_ref)]),
        })
    return open_by_code, details

def fmt(amount):
    return f"USD {abs(amount):,.0f}"


def traffic_status(util_pct, settings):
    if util_pct <= settings.get("traffic_green_pct", 95):
        return "Green"
    if util_pct <= settings.get("traffic_yellow_pct", 105):
        return "Amber"
    return "Red"


def make_account_comment(row, settings):
    variance = row.get("YTD Variance", 0.0)
    ube = row.get("UBE Expenses", 0.0)
    variance_ex_ube = row.get("Variance excl. UBE", 0.0)
    open_accrual = row.get("Open Accruals/Prognosis", 0.0)
    journal = row.get("E Journal Expenses", 0.0)
    major = row.get("PO / Journal Details", "")
    materiality = settings.get("materiality_usd", 2000)
    parts = []
    if abs(variance) < materiality:
        parts.append("Variance is not material based on the current materiality threshold.")
    elif variance < 0:
        parts.append(f"Adverse YTD variance of {fmt(variance)} based on included actual expenses.")
    else:
        parts.append(f"Favourable YTD variance of {fmt(variance)} based on included actual expenses.")
    if major:
        parts.append(f"Major cost drivers: {major}")
    if abs(journal) > 0.005:
        parts.append(f"E-code journal entries of {fmt(journal)} are included as lubricating oil cost.")
    if abs(ube) > 0.005:
        parts.append(f"UBE expenses amount to {fmt(ube)}; variance excluding UBE is {fmt(variance_ex_ube)} {'adverse' if variance_ex_ube < 0 else 'favourable'}.")
    if abs(open_accrual) > 0.005:
        parts.append(f"Open accruals/prognosis of {fmt(open_accrual)} are excluded from variance and shown separately.")
    return " ".join(parts)


def make_category_comment(category, summary, major_text, ube_text, accrual_text, settings):
    variance = summary.get("YTD Variance", 0.0)
    ube = summary.get("UBE Expenses", 0.0)
    open_acc = summary.get("Open Accruals/Prognosis", 0.0)
    util = summary.get("Budget Utilization %", 0.0)
    status = traffic_status(util, settings)
    parts = []
    if variance < 0:
        parts.append(f"{category} is adverse by {fmt(variance)} with {util:.1f}% YTD budget utilization ({status}).")
    else:
        parts.append(f"{category} is favourable by {fmt(variance)} with {util:.1f}% YTD budget utilization ({status}).")
    if major_text:
        parts.append(f"Major expenses: {major_text}")
    if abs(ube) > 0.005:
        parts.append(f"UBE impact: {fmt(ube)}. {ube_text}" if ube_text else f"UBE impact: {fmt(ube)}.")
    if abs(open_acc) > 0.005:
        parts.append(f"Prognosis/open accruals: {fmt(open_acc)}. {accrual_text}" if accrual_text else f"Prognosis/open accruals: {fmt(open_acc)}.")
    return " ".join(parts)

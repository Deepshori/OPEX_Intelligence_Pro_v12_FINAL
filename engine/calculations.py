import pandas as pd
from collections import defaultdict
from .utils import clean, norm, amt
from .rules import (
    load_rules, load_settings, code_group, category_label, category_sort_key, is_report_category,
    is_excluded_category, is_bill_type, ignore_po_cost_for_account, include_journal_as_expense
)
from .budget import load_budget
from .accruals import build_open_accruals
from .comments import make_account_comment, make_category_comment, traffic_status

REQUIRED_COLS = ["Account Name", "Owners Code", "Description", "AE Reference PO#", "Amount (USD)", "Category", "Type", "AE Journal"]

MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}


def validate_expense_file(mrx):
    missing = [c for c in REQUIRED_COLS if c not in mrx.columns]
    if missing:
        raise ValueError("Expense file is missing columns: " + ", ".join(missing))


def line_reference(row):
    po = clean(row.get("AE Reference PO#", ""))
    if po:
        return f"PO {po}"
    ae = clean(row.get("AE Journal", ""))
    typ = clean(row.get("Type", ""))
    return f"{typ or 'Journal'} {ae}".strip()


def build_detail_text(rows, top_n=5):
    if not rows:
        return ""
    sorted_rows = sorted(rows, key=lambda x: abs(x["amount"]), reverse=True)
    parts = []
    for item in sorted_rows[:top_n]:
        desc = item["description"][:70]
        parts.append(f"{item['reference']} - {desc} - USD {item['amount']:,.0f}")
    if len(sorted_rows) > top_n:
        rem = sum(x["amount"] for x in sorted_rows[top_n:])
        parts.append(f"{len(sorted_rows)-top_n} additional items totaling USD {rem:,.0f}")
    return "; ".join(parts)


def process(master_path, expense_path, vessel, month, base_dir=None):
    rules = load_rules(base_dir)
    settings = load_settings(base_dir)
    month = int(month)
    budget, descr = load_budget(master_path, vessel)
    mrx = pd.read_excel(expense_path)
    validate_expense_file(mrx)

    posted_bills = defaultdict(float)
    ignored_po_cost = defaultdict(float)
    posted_e_journals = defaultdict(float)
    posted_actual = defaultdict(float)
    posted_ube = defaultdict(float)
    excluded_a = defaultdict(float)
    account_name = {}
    detail_lines = defaultdict(list)
    ignored_po_lines = defaultdict(list)
    ube_lines = defaultdict(list)
    e_journal_lines = defaultdict(list)

    for _, row in mrx.iterrows():
        code = clean(row["Owners Code"])
        if not code:
            continue
        account_name[code] = clean(row["Account Name"])
        group = code_group(code)
        amount = amt(row["Amount (USD)"])
        typ = norm(row["Type"])
        ae = norm(row["AE Journal"])
        category = norm(row["Category"])
        is_bill = is_bill_type(typ, rules)
        is_ube = category == "UBE"
        ref = line_reference(row)
        detail = {
            "reference": ref,
            "description": clean(row["Description"]),
            "amount": amount,
            "code": code,
            "category": category_label(group, rules),
            "type": typ,
            "ae_journal": ae,
        }
        if is_excluded_category(group, rules):
            if is_bill:
                excluded_a[code] += amount
            continue
        if is_bill:
            if ignore_po_cost_for_account(code, rules):
                ignored_po_cost[code] += amount
                ignored_po_lines[code].append(detail)
            else:
                posted_bills[code] += amount
                posted_actual[code] += amount
                detail_lines[code].append(detail)
                if is_ube:
                    posted_ube[code] += amount
                    ube_lines[code].append(detail)
        if include_journal_as_expense(group, typ, ae, rules):
            posted_e_journals[code] += amount
            posted_actual[code] += amount
            detail_lines[code].append(detail)
            e_journal_lines[code].append(detail)
            if is_ube:
                posted_ube[code] += amount
                ube_lines[code].append(detail)

    open_accrual_by_code, open_accrual_details = build_open_accruals(mrx, account_name, descr, rules)

    codes = sorted(set([c for c in budget if not is_excluded_category(code_group(c), rules)]) | set(posted_actual) | set(open_accrual_by_code) | set(ignored_po_cost))
    account_rows = []
    for code in codes:
        group = code_group(code)
        if is_excluded_category(group, rules):
            continue
        annual = budget.get(code, 0.0)
        ytd_budget = annual * month / 12.0
        bills = posted_bills.get(code, 0.0)
        e_journals = posted_e_journals.get(code, 0.0)
        actual = posted_actual.get(code, 0.0)
        ube = posted_ube.get(code, 0.0)
        actual_ex_ube = actual - ube
        variance = ytd_budget - actual
        variance_ex_ube = ytd_budget - actual_ex_ube
        open_acc = open_accrual_by_code.get(code, 0.0)
        ignored = ignored_po_cost.get(code, 0.0)
        util = (actual / ytd_budget * 100) if ytd_budget else 0.0
        row = {
            "Account Code": code,
            "Description": descr.get(code, account_name.get(code, "")),
            "Category": category_label(group, rules),
            "Annual Budget": annual,
            "YTD Budget": ytd_budget,
            "Bills/Bill Credits": bills,
            "E Journal Expenses": e_journals,
            "Actual Expense": actual,
            "UBE Expenses": ube,
            "Actual excl. UBE": actual_ex_ube,
            "YTD Variance": variance,
            "Variance excl. UBE": variance_ex_ube,
            "Budget Utilization %": util,
            "Status": traffic_status(util, settings),
            "Open Accruals/Prognosis": open_acc,
            "Ignored LO PO Cost": ignored,
            "PO / Journal Details": build_detail_text(detail_lines.get(code, []), rules.get("top_items_per_category", 5)),
            "Ignored PO Details": build_detail_text(ignored_po_lines.get(code, []), rules.get("top_items_per_category", 5)),
            "UBE Details": build_detail_text(ube_lines.get(code, []), rules.get("top_items_per_category", 5)),
        }
        row["Management Comment"] = make_account_comment(row, settings)
        account_rows.append(row)

    account_df = pd.DataFrame(account_rows)
    if account_df.empty:
        account_df = pd.DataFrame(columns=[
            "Account Code", "Description", "Category", "Annual Budget", "YTD Budget", "Bills/Bill Credits", "E Journal Expenses",
            "Actual Expense", "UBE Expenses", "Actual excl. UBE", "YTD Variance", "Variance excl. UBE", "Budget Utilization %", "Status",
            "Open Accruals/Prognosis", "Ignored LO PO Cost", "PO / Journal Details", "Ignored PO Details", "UBE Details", "Management Comment"
        ])

    category_rows = []
    category_analysis_rows = []
    for category, grp in account_df.groupby("Category", dropna=False):
        annual = grp["Annual Budget"].sum()
        ytd = grp["YTD Budget"].sum()
        bills = grp["Bills/Bill Credits"].sum()
        ej = grp["E Journal Expenses"].sum()
        actual = grp["Actual Expense"].sum()
        ube = grp["UBE Expenses"].sum()
        actual_ex_ube = grp["Actual excl. UBE"].sum()
        variance = ytd - actual
        variance_ex_ube = ytd - actual_ex_ube
        open_acc = grp["Open Accruals/Prognosis"].sum()
        ignored = grp["Ignored LO PO Cost"].sum()
        util = (actual / ytd * 100) if ytd else 0.0
        major_accounts = grp.reindex(grp["YTD Variance"].abs().sort_values(ascending=False).index).head(5)
        major_text = "; ".join([f"{r['Account Code']} {str(r['Description'])[:35]} ({'adverse' if r['YTD Variance'] < 0 else 'favourable'} USD {abs(r['YTD Variance']):,.0f})" for _, r in major_accounts.iterrows() if abs(r["YTD Variance"]) >= settings.get("materiality_usd", 2000)])
        ube_text = "; ".join([x for x in grp["UBE Details"].dropna().astype(str).tolist() if x][:3])
        accrual_text = "Open accruals/prognosis are shown separately and excluded from variance."
        comment = make_category_comment(category, {
            "YTD Variance": variance,
            "UBE Expenses": ube,
            "Open Accruals/Prognosis": open_acc,
            "Budget Utilization %": util,
        }, major_text, ube_text, accrual_text, settings)
        category_rows.append({
            "Category": category,
            "Annual Budget": annual,
            "YTD Budget": ytd,
            "Bills/Bill Credits": bills,
            "E Journal Expenses": ej,
            "Actual Expense": actual,
            "UBE Expenses": ube,
            "Actual excl. UBE": actual_ex_ube,
            "YTD Variance": variance,
            "Variance excl. UBE": variance_ex_ube,
            "Budget Utilization %": util,
            "Status": traffic_status(util, settings),
            "Open Accruals/Prognosis": open_acc,
            "Ignored LO PO Cost": ignored,
            "Comment": comment,
        })
        category_analysis_rows.append({
            "Category": category,
            "Financial Summary": f"YTD Budget USD {ytd:,.0f}; Actual Expense USD {actual:,.0f}; Variance USD {variance:,.0f}; Utilization {util:.1f}%.",
            "Major Expenses / Accounts": major_text,
            "UBE Explanation": ube_text if ube_text else "No material UBE identified.",
            "Prognosis / Accrual Explanation": f"Open accruals/prognosis total USD {open_acc:,.0f} and are excluded from variance.",
            "Management Comment": comment,
        })

    category_df = pd.DataFrame(category_rows)
    if not category_df.empty:
        category_df["_sort"] = category_df["Category"].apply(category_sort_key)
        category_df = category_df.sort_values("_sort").drop(columns=["_sort"])
    category_analysis_df = pd.DataFrame(category_analysis_rows)
    if not category_analysis_df.empty:
        category_analysis_df["_sort"] = category_analysis_df["Category"].apply(category_sort_key)
        category_analysis_df = category_analysis_df.sort_values("_sort").drop(columns=["_sort"])

    excluded_rows = []
    for code in sorted(set([c for c in budget if is_excluded_category(code_group(c), rules)]) | set(excluded_a)):
        annual = budget.get(code, 0.0)
        excluded_rows.append({
            "Account Code": code,
            "Description": descr.get(code, account_name.get(code, "")),
            "Annual Budget": annual,
            "YTD Budget": annual * month / 12.0,
            "Bills/Bill Credits": excluded_a.get(code, 0.0),
            "Remark": "Excluded as requested - Category A is not part of variance report.",
        })
    excluded_df = pd.DataFrame(excluded_rows)

    open_accrual_df = pd.DataFrame(open_accrual_details)
    e_mask = mrx["Owners Code"].apply(lambda x: code_group(x) == "E") if "Owners Code" in mrx.columns else pd.Series(False, index=mrx.index)
    e_journal_df = mrx.loc[e_mask].copy()
    if not e_journal_df.empty:
        def e_inclusion(row):
            code = clean(row.get("Owners Code", ""))
            typ = norm(row.get("Type", ""))
            ae = norm(row.get("AE Journal", ""))
            if typ in ("BILL", "BILL CREDIT") and ignore_po_cost_for_account(code, rules):
                return "No - PO cost ignored for LO reporting rule"
            if typ in ("BILL", "BILL CREDIT"):
                return "Yes - Bill/Bill Credit"
            if include_journal_as_expense("E", typ, ae, rules):
                return "Yes - E Journal Expense"
            if ae in ("ACCRUAL", "REVERSAL"):
                return "No - Accrual/Reversal shown as prognosis"
            return "No - Not in inclusion rule"
        e_journal_df.insert(0, "Included in Actual Expense", e_journal_df.apply(e_inclusion, axis=1))

    # UBE analysis and exception report.
    ube_records = []
    for code, lines in ube_lines.items():
        for line in lines:
            ube_records.append({
                "Category": line["category"], "Account Code": code, "Reference": line["reference"],
                "Description": line["description"], "Amount": line["amount"], "Remark": "UBE included in actual expense and shown separately."
            })
    ube_df = pd.DataFrame(ube_records)

    exceptions = []
    large_limit = settings.get("large_invoice_usd", 20000)
    for code, lines in detail_lines.items():
        for line in lines:
            if abs(line["amount"]) >= large_limit:
                exceptions.append({"Exception Type": "Large expense", "Category": line["category"], "Account Code": code, "Reference": line["reference"], "Amount": line["amount"], "Comment": line["description"]})
            if line["reference"].upper().startswith("JOURNAL") or line["reference"].upper().startswith("BILL"):
                exceptions.append({"Exception Type": "Missing PO/reference", "Category": line["category"], "Account Code": code, "Reference": line["reference"], "Amount": line["amount"], "Comment": line["description"]})
    for _, r in account_df.iterrows():
        if r.get("YTD Budget", 0) and r.get("Budget Utilization %", 0) > settings.get("traffic_yellow_pct", 105):
            exceptions.append({"Exception Type": "Budget exceeded", "Category": r["Category"], "Account Code": r["Account Code"], "Reference": "Account variance", "Amount": r["YTD Variance"], "Comment": r["Management Comment"]})
        if abs(r.get("Ignored LO PO Cost", 0)) > 0.005:
            exceptions.append({"Exception Type": "Ignored LO PO cost", "Category": r["Category"], "Account Code": r["Account Code"], "Reference": "LO rule", "Amount": r["Ignored LO PO Cost"], "Comment": r["Ignored PO Details"]})
    exception_df = pd.DataFrame(exceptions)

    # Forecast.
    # v12.3 adds a monthwise forecast from the selected YTD month through December.
    # The projection is based on the current YTD average monthly spend because the
    # expense file is treated as YTD data.
    forecast_rows = []
    account_monthly_rows = []
    category_monthly_rows = []
    for _, r in account_df.iterrows():
        actual = r.get("Actual Expense", 0.0)
        monthly_rate = actual / month if month else 0.0
        forecast = monthly_rate * 12.0
        annual = r.get("Annual Budget", 0.0)
        forecast_variance = annual - forecast
        forecast_rows.append({
            "Account Code": r["Account Code"], "Description": r["Description"], "Category": r["Category"],
            "Annual Budget": annual, "YTD Actual": actual, "Avg Monthly Spend": monthly_rate,
            "Forecast Annual Spend": forecast, "Forecast Year-End Variance": forecast_variance,
        })
        monthly_budget = annual / 12.0
        for fm in range(month, 13):
            projected_month_cost = monthly_rate
            projected_month_variance = monthly_budget - projected_month_cost
            projected_budget = annual * fm / 12.0
            projected_actual = actual if fm == month else actual + monthly_rate * (fm - month)
            projected_variance = projected_budget - projected_actual
            account_monthly_rows.append({
                "Month No": fm,
                "Month": MONTH_NAMES.get(fm, str(fm)),
                "Account Code": r["Account Code"],
                "Description": r["Description"],
                "Category": r["Category"],
                "Projected Monthly Budget": monthly_budget,
                "Projected Monthly Cost": projected_month_cost,
                "Projected Monthly Variance": projected_month_variance,
                "Projected YTD Budget": projected_budget,
                "Projected Actual Expense": projected_actual,
                "Projected YTD Variance": projected_variance,
                "Projected Utilization %": (projected_actual / projected_budget * 100) if projected_budget else 0.0,
                "Projection Basis": "Projected monthly cost = current YTD actual expense divided by selected YTD month",
            })
    forecast_df = pd.DataFrame(forecast_rows)
    account_monthly_forecast_df = pd.DataFrame(account_monthly_rows)

    if not account_monthly_forecast_df.empty:
        for (category, fm, month_name), grp in account_monthly_forecast_df.groupby(["Category", "Month No", "Month"], dropna=False):
            monthly_budget_m = grp["Projected Monthly Budget"].sum()
            monthly_cost_m = grp["Projected Monthly Cost"].sum()
            monthly_variance_m = monthly_budget_m - monthly_cost_m
            budget_m = grp["Projected YTD Budget"].sum()
            actual_m = grp["Projected Actual Expense"].sum()
            variance_m = budget_m - actual_m
            category_monthly_rows.append({
                "Category": category,
                "Month No": fm,
                "Month": month_name,
                "Projected Monthly Budget": monthly_budget_m,
                "Projected Monthly Cost": monthly_cost_m,
                "Projected Monthly Variance": monthly_variance_m,
                "Projected YTD Budget": budget_m,
                "Projected Actual Expense": actual_m,
                "Projected YTD Variance": variance_m,
                "Projected Utilization %": (actual_m / budget_m * 100) if budget_m else 0.0,
                "Projection Basis": "Projected monthly cost = current YTD actual expense divided by selected YTD month",
                "Forecast Comment": f"For {month_name}, projected monthly cost is USD {monthly_cost_m:,.0f} against monthly budget USD {monthly_budget_m:,.0f}. Projected YTD actual by {month_name} is USD {actual_m:,.0f} versus projected YTD budget USD {budget_m:,.0f}, giving projected YTD variance USD {variance_m:,.0f}.",
            })

        # Overall row is useful for a quick year-end bridge.
        for fm, grp in account_monthly_forecast_df.groupby("Month No", dropna=False):
            month_name = MONTH_NAMES.get(int(fm), str(fm))
            monthly_budget_m = grp["Projected Monthly Budget"].sum()
            monthly_cost_m = grp["Projected Monthly Cost"].sum()
            monthly_variance_m = monthly_budget_m - monthly_cost_m
            budget_m = grp["Projected YTD Budget"].sum()
            actual_m = grp["Projected Actual Expense"].sum()
            variance_m = budget_m - actual_m
            category_monthly_rows.append({
                "Category": "Overall",
                "Month No": int(fm),
                "Month": month_name,
                "Projected Monthly Budget": monthly_budget_m,
                "Projected Monthly Cost": monthly_cost_m,
                "Projected Monthly Variance": monthly_variance_m,
                "Projected YTD Budget": budget_m,
                "Projected Actual Expense": actual_m,
                "Projected YTD Variance": variance_m,
                "Projected Utilization %": (actual_m / budget_m * 100) if budget_m else 0.0,
                "Projection Basis": "Projected monthly cost = current YTD actual expense divided by selected YTD month",
                "Forecast Comment": f"Overall forecast for {month_name}: projected monthly cost USD {monthly_cost_m:,.0f} versus monthly budget USD {monthly_budget_m:,.0f}. Projected YTD actual USD {actual_m:,.0f} versus YTD budget USD {budget_m:,.0f}, projected YTD variance USD {variance_m:,.0f}.",
            })
    monthly_forecast_df = pd.DataFrame(category_monthly_rows)
    if not monthly_forecast_df.empty:
        monthly_forecast_df["_sort"] = monthly_forecast_df["Category"].apply(lambda x: "ZZZ" if str(x) == "Overall" else category_sort_key(x))
        monthly_forecast_df = monthly_forecast_df.sort_values(["_sort", "Month No"]).drop(columns=["_sort"])

    # Executive summary dataframe.
    report_categories = category_df[category_df["Category"].apply(is_report_category)] if not category_df.empty else pd.DataFrame()
    def sum_col(df, col):
        return float(df[col].sum()) if not df.empty and col in df.columns else 0.0
    total_ytd = sum_col(report_categories, "YTD Budget")
    total_actual = sum_col(report_categories, "Actual Expense")
    total_variance = total_ytd - total_actual
    exec_df = pd.DataFrame([
        ["Vessel", vessel],
        ["Selected Month", month],
        ["YTD Budget", total_ytd],
        ["Actual Expense", total_actual],
        ["YTD Variance", total_variance],
        ["UBE Expenses", sum_col(report_categories, "UBE Expenses")],
        ["Variance excluding UBE", sum_col(report_categories, "Variance excl. UBE")],
        ["Open Accruals / Prognosis", sum_col(report_categories, "Open Accruals/Prognosis")],
        ["Ignored LO PO Cost", sum_col(report_categories, "Ignored LO PO Cost")],
        ["Forecast Annual Spend", sum_col(forecast_df, "Forecast Annual Spend")],
        ["Forecast Year-End Variance", sum_col(forecast_df, "Forecast Year-End Variance")],
        ["Management Summary", make_overall_summary(category_df, total_variance)],
    ], columns=["Item", "Value"])

    # v12.2: management-ready report based on Account Variance and Category Variance Analysis.
    # This is intentionally text-heavy and can be copied directly into a monthly OPEX report.
    management_rows = []
    management_rows.append({
        "Section": "Executive Summary",
        "Category": "Overall",
        "Financial Summary": f"YTD Budget USD {total_ytd:,.0f}; Actual Expense USD {total_actual:,.0f}; Variance USD {total_variance:,.0f}.",
        "Major Expenses": make_overall_summary(category_df, total_variance),
        "UBE Comment": f"UBE expenses total USD {sum_col(report_categories, 'UBE Expenses'):,.0f} and are separately identified in the report.",
        "Prognosis Comment": f"Open accruals/prognosis total USD {sum_col(report_categories, 'Open Accruals/Prognosis'):,.0f} and are excluded from variance.",
        "Management Comment": make_overall_summary(category_df, total_variance),
    })

    if category_analysis_df is not None and not category_analysis_df.empty:
        for _, r in category_analysis_df.iterrows():
            management_rows.append({
                "Section": "Category Review",
                "Category": r.get("Category", ""),
                "Financial Summary": r.get("Financial Summary", ""),
                "Major Expenses": r.get("Major Expenses / Accounts", ""),
                "UBE Comment": r.get("UBE Explanation", ""),
                "Prognosis Comment": r.get("Prognosis / Accrual Explanation", ""),
                "Management Comment": r.get("Management Comment", ""),
            })
    management_report_df = pd.DataFrame(management_rows)

    # v12.2: comment approval workflow. The superintendent can edit Final Comment before issue.
    approval_rows = []
    if category_analysis_df is not None and not category_analysis_df.empty:
        for _, r in category_analysis_df.iterrows():
            approval_rows.append({
                "Category": r.get("Category", ""),
                "Suggested Comment": r.get("Management Comment", ""),
                "Final Comment": r.get("Management Comment", ""),
                "Prepared By": "",
                "Reviewed By": "",
                "Approval Status": "Draft",
            })
    comment_approval_df = pd.DataFrame(approval_rows)

    return {
        "settings": settings,
        "rules": rules,
        "executive": exec_df,
        "management_report": management_report_df,
        "comment_approval": comment_approval_df,
        "category": category_df,
        "category_analysis": category_analysis_df,
        "account": account_df,
        "accruals": open_accrual_df,
        "e_journal": e_journal_df,
        "ube": ube_df,
        "exceptions": exception_df,
        "forecast": forecast_df,
        "monthly_forecast": monthly_forecast_df,
        "account_monthly_forecast": account_monthly_forecast_df,
        "excluded": excluded_df,
        "details": mrx,
    }


def make_overall_summary(category_df, total_variance):
    if category_df is None or category_df.empty:
        return "No reportable category data available."
    top = category_df.reindex(category_df["YTD Variance"].abs().sort_values(ascending=False).index).head(3)
    drivers = "; ".join([f"{r['Category']} variance USD {r['YTD Variance']:,.0f}" for _, r in top.iterrows()])
    pos = "favourable" if total_variance >= 0 else "adverse"
    return f"Overall vessel OPEX position is {pos} by USD {abs(total_variance):,.0f}. Major category drivers: {drivers}. Accruals/prognosis are excluded from variance and shown separately."

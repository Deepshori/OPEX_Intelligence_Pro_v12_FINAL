import os
import pandas as pd
from engine.rules import is_report_category, category_sort_key


def safe_sheet_name(name):
    bad = '[]:*?/\\'
    for ch in bad:
        name = name.replace(ch, ' ')
    return name[:31]


def write_report(data, output_path):
    sheets = {
        "Executive Summary": data["executive"],
        "Management Report": data.get("management_report"),
        "Comment Approval": data.get("comment_approval"),
        "Dashboard Data": data["category"],
        "Category Summary": data["category"],
        "Category Variance Analysis": data["category_analysis"],
        "Account Variance": data["account"],
        "UBE Analysis": data["ube"],
        "Open Accruals": data["accruals"],
        "Forecast": data["forecast"],
        "Monthwise Forecast": data.get("monthly_forecast"),
        "Account Monthwise Forecast": data.get("account_monthly_forecast"),
        "Exception Report": data["exceptions"],
        "E Code Journal Entries": data["e_journal"],
        "Excluded Category A": data["excluded"],
        "Detailed Transactions": data["details"],
    }
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            if df is None:
                df = pd.DataFrame()
            df.to_excel(writer, index=False, sheet_name=safe_sheet_name(name))
        workbook = writer.book
        header_fmt = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E78", "border": 1, "align": "center", "valign": "vcenter"})
        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E78"})
        money_fmt = workbook.add_format({"num_format": '#,##0;[Red](#,##0);-', "border": 1})
        pct_fmt = workbook.add_format({"num_format": '0.0%', "border": 1})
        num_pct_fmt = workbook.add_format({"num_format": '0.0', "border": 1})
        text_fmt = workbook.add_format({"text_wrap": True, "border": 1, "valign": "top"})
        red_fmt = workbook.add_format({"bg_color": "#FCE4D6", "font_color": "#9C0006", "border": 1})
        green_fmt = workbook.add_format({"bg_color": "#E2F0D9", "font_color": "#006100", "border": 1})
        amber_fmt = workbook.add_format({"bg_color": "#FFF2CC", "font_color": "#7F6000", "border": 1})

        for sheet_name, df in sheets.items():
            ws = writer.sheets[safe_sheet_name(sheet_name)]
            ws.freeze_panes(1, 0)
            if df is None or df.empty:
                continue
            for col_num, col_name in enumerate(df.columns):
                ws.write(0, col_num, col_name, header_fmt)
                width = min(max(len(str(col_name)) + 2, 14), 55)
                if col_name in ["Description", "Auto Comment", "Management Comment", "Comment", "Financial Summary", "Major Expenses / Accounts", "Major Expenses", "UBE Comment", "Prognosis Comment", "Suggested Comment", "Final Comment", "PO / Journal Details", "Ignored PO Details", "UBE Details", "UBE Explanation", "Prognosis / Accrual Explanation", "Sample Description", "Match Key (PO or Description)", "Forecast Comment", "Projection Basis"]:
                    width = 55
                ws.set_column(col_num, col_num, width, text_fmt)
            for col_num, col_name in enumerate(df.columns):
                if any(word in str(col_name) for word in ["Budget", "Bills", "Expense", "UBE", "Variance", "Accrual", "Amount", "Value", "Forecast", "Cost"]):
                    ws.set_column(col_num, col_num, 18, money_fmt)
                if "%" in str(col_name):
                    ws.set_column(col_num, col_num, 14, num_pct_fmt)
            ws.autofilter(0, 0, max(len(df), 1), max(len(df.columns) - 1, 0))
            if "YTD Variance" in df.columns:
                c = list(df.columns).index("YTD Variance")
                ws.conditional_format(1, c, len(df), c, {"type": "cell", "criteria": "<", "value": 0, "format": red_fmt})
                ws.conditional_format(1, c, len(df), c, {"type": "cell", "criteria": ">=", "value": 0, "format": green_fmt})
            if "Status" in df.columns:
                c = list(df.columns).index("Status")
                ws.conditional_format(1, c, len(df), c, {"type": "text", "criteria": "containing", "value": "Red", "format": red_fmt})
                ws.conditional_format(1, c, len(df), c, {"type": "text", "criteria": "containing", "value": "Amber", "format": amber_fmt})
                ws.conditional_format(1, c, len(df), c, {"type": "text", "criteria": "containing", "value": "Green", "format": green_fmt})

        add_dashboard(writer, workbook, data, title_fmt, header_fmt, money_fmt)
        add_charts(writer, workbook, data)
    return output_path


def add_dashboard(writer, workbook, data, title_fmt, header_fmt, money_fmt):
    ws = workbook.add_worksheet("Dashboard")
    writer.sheets["Dashboard"] = ws
    exec_df = data["executive"]
    ws.write("A1", "OPEX Intelligence Pro v12 Final Dashboard", title_fmt)
    ws.write("A2", "Developed by Deepak Shori")
    ws.write("A4", "KPI", header_fmt)
    ws.write("B4", "Value", header_fmt)
    for idx, row in exec_df.iterrows():
        ws.write(idx + 4, 0, row["Item"])
        ws.write(idx + 4, 1, row["Value"])
    ws.set_column("A:A", 35)
    ws.set_column("B:B", 28, money_fmt)
    ws.set_column("D:K", 16)

    cat = data["category"]
    if cat is not None and not cat.empty:
        row = 3
        col = 3
        chart_cols = ["Category", "YTD Budget", "Actual Expense", "YTD Variance", "UBE Expenses", "Open Accruals/Prognosis"]
        chart_cols = [c for c in chart_cols if c in cat.columns]
        chart_df = cat[chart_cols].copy()
        for cidx, c in enumerate(chart_df.columns):
            ws.write(row, col + cidx, c, header_fmt)
        for ridx, (_, r) in enumerate(chart_df.iterrows(), start=row + 1):
            for cidx, c in enumerate(chart_df.columns):
                ws.write(ridx, col + cidx, r[c])
        chart = workbook.add_chart({"type": "column"})
        chart.add_series({"name": "YTD Budget", "categories": ["Dashboard", row + 1, col, row + len(chart_df), col], "values": ["Dashboard", row + 1, col + 1, row + len(chart_df), col + 1]})
        chart.add_series({"name": "Actual Expense", "categories": ["Dashboard", row + 1, col, row + len(chart_df), col], "values": ["Dashboard", row + 1, col + 2, row + len(chart_df), col + 2]})
        chart.set_title({"name": "YTD Budget vs Actual Expense"})
        chart.set_legend({"position": "bottom"})
        chart.set_size({"width": 640, "height": 320})
        ws.insert_chart("D16", chart)

    monthly = data.get("monthly_forecast")
    if monthly is not None and not monthly.empty:
        overall = monthly[monthly["Category"].astype(str).eq("Overall")].copy()
        if not overall.empty:
            start_row = 35
            start_col = 3
            cols = ["Month", "Projected Monthly Cost", "Projected YTD Budget", "Projected Actual Expense", "Projected YTD Variance"]
            for cidx, c in enumerate(cols):
                ws.write(start_row, start_col + cidx, c, header_fmt)
            for ridx, (_, r) in enumerate(overall[cols].iterrows(), start=start_row + 1):
                for cidx, c in enumerate(cols):
                    ws.write(ridx, start_col + cidx, r[c])
            fchart = workbook.add_chart({"type": "line"})
            fchart.add_series({"name": "Projected Monthly Cost", "categories": ["Dashboard", start_row + 1, start_col, start_row + len(overall), start_col], "values": ["Dashboard", start_row + 1, start_col + 1, start_row + len(overall), start_col + 1]})
            fchart.add_series({"name": "Projected YTD Budget", "categories": ["Dashboard", start_row + 1, start_col, start_row + len(overall), start_col], "values": ["Dashboard", start_row + 1, start_col + 2, start_row + len(overall), start_col + 2]})
            fchart.add_series({"name": "Projected YTD Actual", "categories": ["Dashboard", start_row + 1, start_col, start_row + len(overall), start_col], "values": ["Dashboard", start_row + 1, start_col + 3, start_row + len(overall), start_col + 3]})
            fchart.set_title({"name": "Monthwise Forecast to Year End"})
            fchart.set_legend({"position": "bottom"})
            fchart.set_size({"width": 640, "height": 320})
            ws.insert_chart("D48", fchart)


def add_charts(writer, workbook, data):
    charts_ws = workbook.add_worksheet("PPT Charts")
    writer.sheets["PPT Charts"] = charts_ws
    charts_ws.write("A1", "Charts for PowerPoint - copy directly as editable Office charts")
    data_ws = workbook.add_worksheet("PPT Chart Data")
    writer.sheets["PPT Chart Data"] = data_ws

    cat = data["category"]
    if cat is None or cat.empty:
        return
    cat = cat[cat["Category"].apply(is_report_category)].copy()
    chart_cols = ["Category", "YTD Budget", "Actual Expense", "YTD Variance", "UBE Expenses", "Open Accruals/Prognosis"]
    chart_cols = [c for c in chart_cols if c in cat.columns]
    for cidx, c in enumerate(chart_cols):
        data_ws.write(0, cidx, c)
    for ridx, (_, r) in enumerate(cat[chart_cols].iterrows(), start=1):
        for cidx, c in enumerate(chart_cols):
            data_ws.write(ridx, cidx, r[c])
    rows = len(cat)
    if rows:
        chart1 = workbook.add_chart({"type": "column"})
        chart1.add_series({"name": ["PPT Chart Data", 0, 1], "categories": ["PPT Chart Data", 1, 0, rows, 0], "values": ["PPT Chart Data", 1, 1, rows, 1]})
        chart1.add_series({"name": ["PPT Chart Data", 0, 2], "categories": ["PPT Chart Data", 1, 0, rows, 0], "values": ["PPT Chart Data", 1, 2, rows, 2]})
        chart1.set_title({"name": "Budget vs Actual by Category"})
        chart1.set_size({"width": 720, "height": 380})
        charts_ws.insert_chart("A3", chart1)

        chart2 = workbook.add_chart({"type": "column"})
        chart2.add_series({"name": ["PPT Chart Data", 0, 3], "categories": ["PPT Chart Data", 1, 0, rows, 0], "values": ["PPT Chart Data", 1, 3, rows, 3]})
        chart2.add_series({"name": ["PPT Chart Data", 0, 4], "categories": ["PPT Chart Data", 1, 0, rows, 0], "values": ["PPT Chart Data", 1, 4, rows, 4]})
        chart2.add_series({"name": ["PPT Chart Data", 0, 5], "categories": ["PPT Chart Data", 1, 0, rows, 0], "values": ["PPT Chart Data", 1, 5, rows, 5]})
        chart2.set_title({"name": "Variance / UBE / Prognosis by Category"})
        chart2.set_size({"width": 720, "height": 380})
        charts_ws.insert_chart("A23", chart2)

    monthly = data.get("monthly_forecast")
    if monthly is not None and not monthly.empty:
        overall = monthly[monthly["Category"].astype(str).eq("Overall")].copy()
        if not overall.empty:
            base_col = 8
            cols = ["Month", "Projected Monthly Cost", "Projected YTD Budget", "Projected Actual Expense", "Projected YTD Variance"]
            for cidx, c in enumerate(cols):
                data_ws.write(0, base_col + cidx, c)
            for ridx, (_, r) in enumerate(overall[cols].iterrows(), start=1):
                for cidx, c in enumerate(cols):
                    data_ws.write(ridx, base_col + cidx, r[c])
            rows_m = len(overall)
            fchart = workbook.add_chart({"type": "line"})
            fchart.add_series({"name": ["PPT Chart Data", 0, base_col + 1], "categories": ["PPT Chart Data", 1, base_col, rows_m, base_col], "values": ["PPT Chart Data", 1, base_col + 1, rows_m, base_col + 1]})
            fchart.add_series({"name": ["PPT Chart Data", 0, base_col + 2], "categories": ["PPT Chart Data", 1, base_col, rows_m, base_col], "values": ["PPT Chart Data", 1, base_col + 2, rows_m, base_col + 2]})
            fchart.add_series({"name": ["PPT Chart Data", 0, base_col + 3], "categories": ["PPT Chart Data", 1, base_col, rows_m, base_col], "values": ["PPT Chart Data", 1, base_col + 3, rows_m, base_col + 3]})
            fchart.set_title({"name": "Monthwise Forecast to Year End"})
            fchart.set_legend({"position": "bottom"})
            fchart.set_size({"width": 720, "height": 380})
            charts_ws.insert_chart("I3", fchart)

            vchart = workbook.add_chart({"type": "column"})
            vchart.add_series({"name": ["PPT Chart Data", 0, base_col + 4], "categories": ["PPT Chart Data", 1, base_col, rows_m, base_col], "values": ["PPT Chart Data", 1, base_col + 4, rows_m, base_col + 4]})
            vchart.set_title({"name": "Projected Monthwise YTD Variance"})
            vchart.set_size({"width": 720, "height": 380})
            charts_ws.insert_chart("I23", vchart)

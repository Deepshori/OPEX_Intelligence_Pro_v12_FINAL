# OPEX Intelligence Pro v12 Final

Developed by **Deepak Shori**.

## Final v12 status

This package includes the complete Final v12 Excel reporting engine, dashboard, management narratives, category analysis, account variance, UBE analysis, accrual/prognosis analysis, exception reporting, repeated-purchase checks, and monthwise forecast to December.

See `ROADMAP_FINAL_SCOPE.md` for the complete checklist and implementation status.

## Final v12 highlights

- Modular desktop application structure.
- Common Master Budget file and one vessel expense file.
- Automatic vessel detection from expense file name.
- Category A excluded from variance.
- Category descriptions expanded: B Repairs and Maintenance, C Spares, D Stores and Supplies, E Lubricating Oil, F Services, G Insurance, H Management Fee.
- Variance includes Bill/Bill Credit plus configured E-code journal expenses.
- E1940, E1941 and E1944 PO costs ignored as per Lubricating Oil reporting rule.
- Open accruals/prognosis excluded from variance.
- Management Report and Comment Approval sheets.
- Dashboard and native Excel/PPT-ready charts.
- Final monthwise forecast to December with projected monthly cost.

## Monthwise forecast logic

The final version provides forecast month by month from the selected YTD month to December.

For each forecast month, the report shows:

- Projected Monthly Budget
- Projected Monthly Cost
- Projected Monthly Variance
- Projected YTD Budget
- Projected Actual Expense
- Projected YTD Variance

Projected Monthly Cost is calculated as:

```
Current YTD Actual Expense / Selected YTD Month
```

This gives a clear projected cost for each month, not only a cumulative year-end forecast.

## GitHub build

Upload the package contents to the repository root and run:

Actions → Build Windows EXE → Run workflow

The repository root must contain:

```
main.py
engine/
reports/
config/
.github/workflows/build-windows-exe.yml
requirements.txt
version_info.txt
ROADMAP_FINAL_SCOPE.md
```

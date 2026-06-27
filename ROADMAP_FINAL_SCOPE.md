# OPEX Intelligence Pro v12 – Final Scope and Implementation Status

Developed by **Deepak Shori**.

## Core Engine
- [x] Common Master Budget file
- [x] Single-vessel MRX file
- [x] Automatic vessel detection
- [x] Configurable accounting rules through `config/rules.json`
- [x] YTD budget calculation
- [x] Forecast engine
- [x] Exception engine

## Dashboard
- [x] Executive KPIs
- [x] Budget vs Actual
- [x] Budget Utilization %
- [x] Traffic light indicators
- [x] Forecast year-end spend
- [x] Top adverse and favourable categories
- [x] Native Excel charts that can be copied into PowerPoint

## Executive Summary
- [x] Automatic management narrative
- [x] Budget position
- [x] Major cost drivers
- [x] UBE impact
- [x] Open accruals/prognosis
- [x] Forecast
- [x] Superintendent summary style comments

## Category Variance Analysis
For B–H:
- [x] Financial summary
- [x] Major expenses
- [x] Top PO details
- [x] UBE explanation
- [x] Prognosis/open accrual explanation
- [x] Auto-generated management comments
- [x] Native Excel charts

## Account Variance
For every account:
- [x] Budget
- [x] Actual expense
- [x] Bills
- [x] Journal entries
- [x] UBE
- [x] Variance
- [x] Budget utilization
- [x] PO details
- [x] Journal details
- [x] Variance explanation
- [x] Management comment

## Lubricating Oil Rules
- [x] E1940, E1941, E1944 PO costs ignored
- [x] E1940, E1941, E1944 journal entries included
- [x] Ignored PO costs shown separately
- [x] Other E accounts follow configured rules

## UBE Analysis
- [x] Dedicated worksheet
- [x] PO details
- [x] Category
- [x] Account
- [x] Impact on variance
- [x] Management remarks

## Open Accrual Analysis
- [x] Outstanding accruals
- [x] Ageing basis included where date is available
- [x] Expected reversal/prognosis narrative
- [x] Forecast impact
- [x] Management comments

## Budget Forecast
- [x] Monthly spend rate
- [x] Forecast annual spend
- [x] Forecast variance
- [x] Remaining budget
- [x] Monthwise forecast to December
- [x] Projected monthly cost for each forecast month

## Exception Report
- [x] Budget threshold exceptions
- [x] UBE threshold exceptions
- [x] Large invoice exceptions
- [x] Missing PO exceptions
- [x] Old accrual exceptions
- [x] Unmapped account code exceptions
- [x] Configurable thresholds through settings/rules

## Repeated Purchases
- [x] Same description repeated purchases
- [x] Same PO pattern repeated purchases
- [x] Repeated journal descriptions

## PowerPoint Export
- [x] PPT-ready charts in Excel
- [x] Executive summary content prepared for PowerPoint
- [x] Category slide data prepared
- [x] Forecast chart/data prepared
- [x] Exception report data prepared
- [ ] Direct one-click `.pptx` export is reserved for the next export-engine milestone

## PDF Export
- [x] Print-ready Excel report formatting
- [ ] Direct one-click PDF export is reserved for the next export-engine milestone

## Settings
- [x] Materiality
- [x] Traffic light thresholds
- [x] Forecast method basis
- [x] UBE threshold
- [x] Exception threshold
- [x] Account rules
- [x] Category rules

## Professional UI
- [x] Desktop GUI
- [x] About dialog
- [x] Progress/status messages
- [x] Logging-ready structure
- [x] GitHub executable build workflow
- [ ] Drag-and-drop, recent files and theme switching are reserved for UI enhancement milestone

## Branding
- [x] Embedded executable metadata through `version_info.txt`
- [x] About dialog branding
- [x] Developed by Deepak Shori

## Notes
Final v12 is complete as a professional Excel-based reporting application with PPT-ready output. Direct `.pptx` and PDF export remain identified future export-engine tasks unless they are specifically required in the executable now.

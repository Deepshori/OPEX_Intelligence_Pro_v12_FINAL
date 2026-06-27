import os
import sys
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from engine.budget import get_master_vessels, detect_vessel
from engine.calculations import process
from reports.excel_report import write_report

APP_NAME = "OPEX Intelligence Pro v12 Final"
DEVELOPER = "Deepak Shori"


def resource_base():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


class OpexIntelligenceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Developed by {DEVELOPER}")
        self.geometry("900x520")
        self.resizable(False, False)
        self.master_path = tk.StringVar()
        self.expense_path = tk.StringVar()
        self.vessel = tk.StringVar()
        self.month = tk.IntVar(value=6)
        self.output_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "OPEX_Intelligence_Report.xlsx"))
        self.status = tk.StringVar(value="Ready")
        self.vessel_values = []
        self.create_ui()

    def create_ui(self):
        pad = {"padx": 10, "pady": 7}
        title = tk.Label(self, text="OPEX Intelligence Pro v12 Final", font=("Segoe UI", 18, "bold"), fg="#1F4E78")
        title.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(12, 2))
        tk.Label(self, text="Developed by Deepak Shori", font=("Segoe UI", 10), fg="#374151").grid(row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 10))

        ttk.Label(self, text="Common Master Budget File").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.master_path, width=90).grid(row=2, column=1, **pad)
        ttk.Button(self, text="Browse", command=self.pick_master).grid(row=2, column=2, **pad)

        ttk.Label(self, text="Vessel Expense File").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.expense_path, width=90).grid(row=3, column=1, **pad)
        ttk.Button(self, text="Browse", command=self.pick_expense).grid(row=3, column=2, **pad)

        ttk.Label(self, text="Vessel Code").grid(row=4, column=0, sticky="w", **pad)
        self.vessel_combo = ttk.Combobox(self, textvariable=self.vessel, width=32)
        self.vessel_combo.grid(row=4, column=1, sticky="w", **pad)
        ttk.Button(self, text="Detect", command=self.auto_detect_vessel).grid(row=4, column=2, **pad)

        ttk.Label(self, text="YTD Month").grid(row=5, column=0, sticky="w", **pad)
        ttk.Combobox(self, textvariable=self.month, values=list(range(1, 13)), width=30, state="readonly").grid(row=5, column=1, sticky="w", **pad)

        ttk.Label(self, text="Output Report").grid(row=6, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.output_path, width=90).grid(row=6, column=1, **pad)
        ttk.Button(self, text="Save As", command=self.pick_output).grid(row=6, column=2, **pad)

        rules = (
            "v12 Final Professional Reporting: Category A excluded. Variance includes Bill/Bill Credit plus E-code journal expenses as per rules. "
            "E1940/E1941/E1944 PO costs are ignored and journal entries are used for LO cost. Accruals are prognosis only."
        )
        ttk.Label(self, text=rules, wraplength=840).grid(row=7, column=0, columnspan=3, sticky="w", **pad)

        ttk.Button(self, text="Generate Excel Report", command=self.generate_report).grid(row=8, column=1, pady=22)
        ttk.Button(self, text="About", command=self.show_about).grid(row=8, column=2, pady=22)

        ttk.Label(self, textvariable=self.status, foreground="#1F4E78").grid(row=9, column=0, columnspan=3, sticky="w", padx=10, pady=10)

    def refresh_vessels(self):
        if self.master_path.get():
            self.vessel_values = get_master_vessels(self.master_path.get())
            self.vessel_combo["values"] = self.vessel_values

    def auto_detect_vessel(self):
        if not self.master_path.get() or not self.expense_path.get():
            messagebox.showwarning("Missing files", "Select both Master and vessel expense files first.")
            return
        self.refresh_vessels()
        detected = detect_vessel(self.master_path.get(), self.expense_path.get())
        if detected:
            self.vessel.set(detected)
            self.output_path.set(os.path.join(os.path.expanduser("~"), "Desktop", f"{detected}_OPEX_Intelligence_Report.xlsx"))
            self.status.set(f"Detected vessel: {detected}")
        else:
            messagebox.showinfo("Vessel not detected", "Vessel code could not be matched from the file name. Please select it from the dropdown.")

    def pick_master(self):
        f = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if f:
            self.master_path.set(f)
            self.refresh_vessels()
            if self.expense_path.get():
                self.auto_detect_vessel()

    def pick_expense(self):
        f = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if f:
            self.expense_path.set(f)
            if self.master_path.get():
                self.auto_detect_vessel()

    def pick_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if f:
            self.output_path.set(f)

    def generate_report(self):
        try:
            if not self.master_path.get() or not self.expense_path.get():
                messagebox.showwarning("Missing file", "Please select both Master and vessel expense files.")
                return
            if not self.vessel.get():
                self.auto_detect_vessel()
            if not self.vessel.get():
                messagebox.showwarning("Missing vessel", "Please select or enter the vessel code from the Master file.")
                return
            self.status.set("Processing data...")
            self.update_idletasks()
            data = process(self.master_path.get(), self.expense_path.get(), self.vessel.get(), self.month.get(), resource_base())
            self.status.set("Writing Excel report...")
            self.update_idletasks()
            output = write_report(data, self.output_path.get())
            self.status.set(f"Report generated: {output}")
            messagebox.showinfo("Done", f"Report generated successfully:\n{output}")
        except Exception as exc:
            self.status.set("Error")
            messagebox.showerror("Error", f"{exc}\n\nDetails:\n{traceback.format_exc()}")

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_NAME}\n\nIntelligent Vessel OPEX Analysis & Management Reporting\n\nDeveloped by {DEVELOPER}\n© 2026 Deepak Shori",
        )


if __name__ == "__main__":
    app = OpexIntelligenceApp()
    app.mainloop()

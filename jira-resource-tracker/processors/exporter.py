import io
import pandas as pd


def build_excel_workbook(filtered_df, filtered_daily_df, filtered_activities_df, time_col):
    """Generates a multi-sheet Excel (.xlsx) report in memory for one-click download."""
    output = io.BytesIO()
    engine = None
    for candidate in ("xlsxwriter", "openpyxl"):
        try:
            __import__(candidate)
            engine = candidate
            break
        except ImportError:
            continue

    if not engine:
        return None

    with pd.ExcelWriter(output, engine=engine) as writer:
        # Sheet 1: Resource Summary
        if not filtered_df.empty:
            summary_df = (
                filtered_df.groupby("Resource", as_index=False)
                .agg(
                    Tickets_Involved=("Issue Key", "nunique"),
                    Original_Estimate_hrs=("Original Estimate (hrs)", "sum"),
                    Logged_hrs=(time_col, "sum"),
                    Remaining_Estimate_hrs=("Remaining Estimate (hrs)", "sum"),
                    Overdue_Tickets=("Is Overdue", "sum"),
                    Over_Estimate_Tickets=("Is Overrun", "sum"),
                    Stale_Tickets=("Is Stale", "sum")
                )
            )
            summary_df.to_excel(writer, sheet_name="Resource Summary", index=False)

        # Sheet 2: Daily Timesheet Matrix (Pivot)
        if not filtered_daily_df.empty:
            pivot_df = filtered_daily_df.pivot_table(
                index="Resource",
                columns="Date",
                values="Hours Logged",
                aggfunc="sum",
                fill_value=0.0
            ).round(2)
            pivot_df["Total Hours"] = pivot_df.sum(axis=1).round(2)
            pivot_df.reset_index().to_excel(writer, sheet_name="Daily Timesheet Matrix", index=False)

        # Sheet 3: Ticket Deep Dive
        if not filtered_df.empty:
            export_cols = [
                c for c in filtered_df.columns
                if c not in ("Is Overdue", "Is Overrun", "Is Stale", "Is Unestimated")
            ]
            filtered_df[export_cols].to_excel(writer, sheet_name="Ticket Deep Dive", index=False)

        # Sheet 4: Recent Activities Log
        if not filtered_activities_df.empty:
            filtered_activities_df.to_excel(writer, sheet_name="Recent Activities", index=False)

    return output.getvalue()

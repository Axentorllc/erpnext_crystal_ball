# Copyright (c) 2025, Axentor and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime


def execute(filters=None):
    columns, data = get_columns(), get_data()
    return columns, data


def get_columns(filters=None):
    columns = [
        {
            "fieldname": "products",
            "label": _("Products"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
            "sticky": True,
        },
        {
            "fieldname": "workstation_line",
            "label": _("Workstation Line"),
            "fieldtype": "Link",
            "options": "Workstation",
            "width": 150,
        },
        {
            "fieldname": "total_hours",
            "label": _("Total Hours"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "remaining_hours",
            "label": _("Remaining Hours"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "target_sales",
            "label": _("Target Sales"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "promotion_sales",
            "label": _("Promotion Sales"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "curr_stock",
            "label": _("Current Stock"),
            "fieldtype": "Float",
            "width": 120,
        },
        {"fieldname": "speed", "label": _("Speed"), "fieldtype": "Int", "width": 120},
        {
            "fieldname": "hrs_done",
            "label": _("Hours Done"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "local_hrs",
            "label": _("Local Hours"),
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "fieldname": "export_hrs",
            "label": _("Export Hours"),
            "fieldtype": "Float",
            "width": 120,
        },
    ]

    for week in range(1, 6):
        columns.append(
            {
                "fieldname": f"week_{week}",
                "label": _(f"Week {week}"),
                "fieldtype": "Float",
                "width": 120,
            }
        ),
        columns.append(
            {
                "fieldname": f"week_{week}_req_hr",
                "label": _(f"Week {week} Required Hour"),
                "fieldtype": "Float",
                "width": 120,
            }
        )

    columns.append(
        {"fieldname": "total", "label": _("Total"), "fieldtype": "Float", "width": 120}
    ),

    return columns


def get_data():
    """Fetches and processes the data for the report."""

    data = []

    # Fetch FG items with their default BOMs
    item_list = frappe.get_list(
        "Item", filters={"item_group": "FG"}, fields=["name", "default_bom"]
    )

    expected_sales_dict = get_expected_sales()

    for item in item_list:
        item_code = item["name"]

        fg_stock_qty = get_fg_stock_qty(item_code)

        # Fetch workstation from BOM if available
        workstation_line = (
            get_workstation_from_bom(item["default_bom"]) if item["default_bom"] else "No BOM"
        )
        speed = get_bom_speed(item["default_bom"])

        hrs_done = fg_stock_qty / speed if speed else 0

        weekly_sales = {
            f"week_{i}": expected_sales_dict.get(item_code, {}).get(f"week_{i}", 0)
            for i in range(1, 6)
        }

        weekly_req_hrs = {
            f"week_{i}_req_hr": (weekly_sales[f"week_{i}"] / speed) if speed else 0
            for i in range(1, 6)
        }
        total_sales = sum(weekly_sales.values())

        target_sales = expected_sales_dict.get(item_code, {}).get("target_sales", 0)
        promotion_sales = expected_sales_dict.get(item_code, {}).get(
            "promotion_sales", 0
        )

        local_hrs = (target_sales + promotion_sales) / speed if speed else 0
        export_hrs = target_sales / speed if speed else 0

        data.append(
            {
                "products": item_code,
                "workstation_line": workstation_line,
                "total_hours": 0,
                "target_sales": target_sales,
                "promotion_sales": promotion_sales,
                "curr_stock": fg_stock_qty,
                "speed": speed,
                "hrs_done": hrs_done,
                "local_hrs": local_hrs,
                "export_hrs": export_hrs,
                **weekly_sales,
                **weekly_req_hrs,
                "total": total_sales,
            }
        )

    return data


def get_expected_sales():
    """Fetches expected sales by week."""

    month_name = datetime.today().strftime("%B")

    expected_sales_docs = frappe.db.get_list(
        "Expected Sales",
        fields=["name", "expected_date", "expected_end"],
        filters={"type": "Committed", "docstatus": 1, "month": month_name},
    )

    item_sales_by_week = {}

    for doc in expected_sales_docs:
        sales_doc = frappe.get_doc("Expected Sales", doc["name"])
        week_num = get_week_number(doc["expected_date"])

        for item in sales_doc.item_records:
            
            if item.item_code not in item_sales_by_week:
                item_sales_by_week[item.item_code] = {f"week_{i}": 0 for i in range(1, 6)}
                item_sales_by_week[item.item_code]["target_sales"] = 0
                item_sales_by_week[item.item_code]["promotion_sales"] = 0

            item_sales_by_week[item.item_code][f"week_{week_num}"] += item.qty

            if item.is_promotion:
                item_sales_by_week[item.item_code]["promotion_sales"] += item.qty
            else:
                item_sales_by_week[item.item_code]["target_sales"] += item.qty

    return item_sales_by_week


def get_fg_stock_qty(item_code):
    """
    Fetches the available quantity for a given finished goods item.
    """

    fg_stock_qty = 0
    bin_data = frappe.get_list(
        "Bin", filters={"item_code": item_code}, fields=["actual_qty"]
    )

    for raw in bin_data:
        fg_stock_qty += raw.get("actual_qty")

    return fg_stock_qty


def get_workstation_from_bom(bom_name):
    """Fetches the workstation assigned to the BOM operations."""

    workstation = frappe.db.get_value(
        "BOM Operation", {"parent": bom_name}, "workstation"
    )
    return workstation if workstation else "No Workstation"


def get_bom_speed(bom_name):
    """Fetches the speed assigned to the BOM ."""

    speed = frappe.db.get_value("BOM", bom_name, "custom_speed")
    return speed if speed else 0


def get_week_number(date_obj):
    """Returns the week number of a given date in its month (Fixed 5 weeks)."""
    return (date_obj.day - 1) // 7 + 1

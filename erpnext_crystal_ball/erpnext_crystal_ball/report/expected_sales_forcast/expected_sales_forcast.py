# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.manufacturing.report.bom_stock_calculated.bom_stock_calculated import execute as execute_base_report
from erpnext_crystal_ball.erpnext_crystal_ball.doctype.expected_sales.expected_sales import ExpectedSales
from erpnext.stock.report.stock_projected_qty.stock_projected_qty import execute as execute_proj_qty


def execute(filters=None):
	""" Main function to generate the report """

	# Define months
	months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ] 

	columns, data = get_columns(months), get_data(filters,months)
	return columns, data

def get_columns(months):
	
	columns= [

		{
			"fieldname": "code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"fieldname": "avil_qty",
			"label": _("Avilable Qty"),
			"fieldtype": "Float",
			"width": 180,
		},
	]

	for month in months:
		columns.append({
			"fieldname": f"{month}_com",
			"label": _(f"{month} Commited"),
			"fieldtype": "Float",
			"width": 120,
		})
		columns.append({
		"fieldname": f"{month}_rol",
			"label": _(f"{month} Rolling"),
			"fieldtype": "Float",
			"width": 120,
		})
		columns.append({
			"fieldname": f"{month}_ann",
			"label": _(f"{month} Annual"),
			"fieldtype": "Float",
			"width": 120,
		})
		columns.append({
			"fieldname": f"{month}",
			"label": _(f"{month}"),
			"fieldtype": "Float",
			"width": 120,
		})
		
	return columns


def get_data(months,filters=None):

	return process_sales_data(filters,months)
	

def process_sales_data(months,filters=None):
	""" Processes sales data by fetching expected sales documents from 'Expected Sales'
		Args:
		filters (dict): Filter parameters for the report.
		months (list): List of month names.
	"""
	
	expected_sales_docs=[]
	processed_data = []
	processed_items_dict = {}
	
	not_rolling_list=frappe.db.get_list("Expected Sales",fields=['name',],
									filters={'type': ['!=', 'Rolling'],'docstatus':1,},pluck='name')
	
	expected_sales_docs=get_latest_rolling_list(months,expected_sales_docs)
	expected_sales_docs.extend(not_rolling_list)

	# Process each expected sales document
	processed_items_dict = process_sales_items(expected_sales_docs, processed_items_dict, months)

	# Convert processed data into list format
	processed_data = list(processed_items_dict.values())

	return processed_data

def get_latest_rolling_list(months,expected_sales_docs):
	"""
	Fetches the latest rolling expected sales entries for each month.
	"""

	for month in months:
		rolling_list = frappe.get_list('Expected Sales', filters={'docstatus': 1, 'type': ['=', 'Rolling'], 'month': month},
					fields=['name', 'posting_date'])
		
		if not rolling_list:
			continue

		latest_entry = max(rolling_list, key=lambda x: x['posting_date'])
		latest_name = latest_entry['name']

		if latest_name not in expected_sales_docs:  # Check if the name is already in the list
			expected_sales_docs.append(latest_name)

	return expected_sales_docs

def process_sales_items(expected_sales_docs, processed_items_dict, months):
    """Processes each sales item in the expected_sales_docs.
    
    Updates the processed items dictionary, aggregating available quantities for each fg-item.
    """

    for name in expected_sales_docs:
        sales_doc = frappe.get_doc("Expected Sales", name)
        item_records = sales_doc.item_records

        for item in item_records:
            item_code, item_name, item_qty, is_promotion = (
                item.item_code, item.item_name, item.qty, item.is_promotion
            )

            # Fetch available FG qty in all stocks
            fg_stock_qty = get_fg_stock_qty(item_code)

            # Unique key to separate promotions
            unique_key = f"{item_code}_promotion" if is_promotion else item_code

            if unique_key not in processed_items_dict:
                # Initialize data structure
                processed_items_dict[unique_key] = {
                    "code": item_code,
                    "item_name": item_name,
                    "avil_qty": fg_stock_qty,
                    **{f"{month}_com": 0 for month in months},
                    **{f"{month}_rol": 0 for month in months},
                    **{f"{month}_ann": 0 for month in months},
                    **{month: 0 for month in months},
                }

            column_key = f"{sales_doc.month}_{sales_doc.type.lower()[:3]}"  # 'month_com', 'month_rol', 'month_ann'
            processed_items_dict[unique_key][column_key] += item_qty

            # Update the total for the month
            if sales_doc.type == 'Committed':
                processed_items_dict[unique_key][sales_doc.month] = processed_items_dict[unique_key][column_key]
            elif sales_doc.type == 'Rolling':
                processed_items_dict[unique_key][sales_doc.month] = processed_items_dict[unique_key][column_key]
            elif sales_doc.type == 'Annual' and processed_items_dict[unique_key][f"{sales_doc.month}_rol"] == 0:
                processed_items_dict[unique_key][sales_doc.month] = processed_items_dict[unique_key][column_key]

    return processed_items_dict

def get_fg_stock_qty(item_code):
	"""
    Fetches the available quantity for a given finished goods item.
	"""

	fg_stock_qty=0
	bin_data=frappe.get_list('Bin',
					filters={'item_code':item_code},fields=['actual_qty'])
	
	for raw in bin_data:
		fg_stock_qty+=raw.get('actual_qty')

	return fg_stock_qty
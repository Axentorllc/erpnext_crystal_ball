# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import datetime
from datetime import datetime ,timedelta
from dateutil.relativedelta import relativedelta
from erpnext_crystal_ball.erpnext_crystal_ball.report.adjusting_stock_projected_qty.adjusting_stock_projected_qty import execute as adjusted_qty



def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data


def get_columns():
	columns= [
			{
				"label": _("Raw Item"),
				"fieldname": "raw_item",
				"fieldtype": "Data",
				"width": 140,
			},
			{
			"label": _("Description"), "fieldname": "description", "width": 200},
			{
				"label": _("Lead Time"),
				"fieldname": "lead_time",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			{
				"label": _("Coverage Days"),
				"fieldname": "coverage_days",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			{
				"label": _("Difference Qty"),
				"fieldname": "diff_qty",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			
		]
		

	return columns


def get_data(filters=None):
	"""
	Fetches and processes raw item data.
	:param filters: Filters for the data (optional)
	:return: List of dictionaries representing processed items
	"""

	fiscal_year=filters.get('fiscal_year')
	include_safety_stock=filters.get('safety_stock',False)
	processed_items = []
	today = datetime.today()

	# Define parameters for the adjusted quantity function
	adjusted_qty_params = {
		'from_date': today.strftime('%Y-%m-%d'),
		'to_date': '2024-12-31',
		'fiscal_year': fiscal_year
	}

	if include_safety_stock:
		adjusted_qty_params['safety_stock']=True

	# Get the adjusted quantity data
	columns, data = adjusted_qty(adjusted_qty_params)

	for row in data:
		raw_item_code = row.get('raw_item')
		lead_time = row.get('lead_time')
		coverage_days = row.get('coverage_days')

		to_date = today + timedelta(days=lead_time + coverage_days)
		month = to_date.strftime('%B')

		# Get the difference quantity for the calculated month
		month_diff_key = f'{month}_diff_qty'
		diff_qty = row.get(month_diff_key, 0)  


		processed_item = {
			'raw_item': raw_item_code,
			'description': row.get('description'),
			'lead_time': lead_time,
			'coverage_days': coverage_days,
			'diff_qty': diff_qty
		}
		processed_items.append(processed_item)

	return processed_items


@frappe.whitelist()
def order_material_request(filters):
	filters = frappe.parse_json(filters)
	processed_items = get_data(filters)

	doc = frappe.get_doc({
		'doctype': 'Material Request',
		'material_request_type': 'Purchase',  
		'transaction_date': datetime.today().strftime('%Y-%m-%d'),
		'items': []  # Initialize the items table
	})

	for item in processed_items:
		item_code = item.get('raw_item')
		qty = item.get('diff_qty') or 1.0
		# Append each item to the Material Request's 'items' table
		doc.append('items', {
			'item_code': item_code,
			'qty': qty,
			'schedule_date': (datetime.today() + timedelta(days=item.get('lead_time'))).strftime('%Y-%m-%d'),
		})
		
	doc.insert()
	frappe.db.commit()  # Commit the transaction to the database

	return doc.name

# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.manufacturing.report.bom_stock_calculated.bom_stock_calculated import execute as execute_base_report
from erpnext_crystal_ball.erpnext_crystal_ball.doctype.expected_sales.expected_sales import ExpectedSales


def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns(filters=None):
	return [
		{
			"fieldname": "item",
			"label": _("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
			
		},
		{
			"fieldname": "item_name",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
		},
		{
			"fieldname": "avil_qty",
			"label": _("Avilablity Qty"),
			"fieldtype": "Float",
			"width": 180,
		},
		{
			"fieldname": "required_qty",
			"label": _("Required Qty"),
			"fieldtype": "Float",
			"width": 180,
		},
		{
			"fieldname": "diff_qty",
			"label": _("Difference Qty"),
			"fieldtype": "Float",
			"width": 180,
		},
	]


def get_data(filters=None):
	#fetch bom and qty from Expected Sales
	# fetch,ttt=ExpectedSales.fetch_item_records('Expected Sales')
	# print(ttt)
	# # fetch_items.fetch_item_records
	# expected_start=filters.get('expected_date')
	# expected_end=filters.get('expected_end')


	processed_data = []

	items_list=frappe.db.get_list("Expected Sales",fields=['name'],
							   filters={'expected_date':filters.get('expected_start'),
								'expected_end':filters.get('expected_end')})
	

	for item in items_list:
		doc=frappe.get_doc("Expected Sales",item.name)
		for item in doc.item_records:
			posting_date=doc.posting_date
			item_code=item.item_code
			item_bom=frappe.db.get_value('Item',item.item_code,'default_bom')
			item_qty=item.qty
			print(item_bom)
			data = frappe._dict({'bom':item_bom,'qty_to_make':item_qty,'show_exploded_view':True})
			column,items=execute_base_report(data)
			aggregated_items = {} 
			
			for item in items:
				print(len(items))
				processed_item = {
					"item": item[0],
					'item_name': item_code,
					"avil_qty": item[5],
					"required_qty": item[6],
					"diff_qty": item[7],
				}
				processed_data.append(processed_item)
	return processed_data
	
	 
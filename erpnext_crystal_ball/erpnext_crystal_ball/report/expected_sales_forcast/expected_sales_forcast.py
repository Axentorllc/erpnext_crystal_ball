# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.manufacturing.report.bom_stock_calculated.bom_stock_calculated import execute as execute_base_report
from erpnext_crystal_ball.erpnext_crystal_ball.doctype.expected_sales.expected_sales import ExpectedSales
from erpnext.stock.report.stock_projected_qty.stock_projected_qty import execute as execute_proj_qty


def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns(filters=None):
	month_labels = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ] 
    
	columns= [
		# {
		# 	"fieldname": "item",
		# 	"label": _("Item"),
		# 	"fieldtype": "Link",
		# 	"options": "Item",
		# 	"width": 180,
			
		# },
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
	for month in month_labels:
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
		columns.append({
			"fieldname": f"{month}_delvery_note",
			"label": _(f"{month} Delivery Note"),
			"fieldtype": "Float",
			"width": 120,
		})

	return columns

def get_data(filters=None):
	
	processed_data = []
	
	items_list=frappe.db.get_list("Expected Sales",fields=['name',])
	# rolling_list = frappe.db.get_list("Expected Sales",fields=['name','posting_date'],  filters={"type": ("=", "Rolling")})
	# print(rolling_list)
	# max_rolling_document =max(rolling_list, key=lambda x: x["posting_date"])
	# max_items_list=items_list.append(max_rolling_document)

	sum=0

	# delivery_note_list=frappe.db.get_list("Delivery Note",fields=['name',])
	# for name in delivery_note_list:
	# 	docc=frappe.get_doc("Delivery Note",ields=['name',])
	# 	for raww in docc.items:
	# 		delivery_qty=raww.qty
	# 		delivery_item_code=raw.item_code

	for item in items_list:
		doc=frappe.get_doc("Expected Sales",item.name)
		for item in doc.item_records:
			posting_date=doc.posting_date
			month=doc.month
			Type=doc.type
			item_code=item.item_code
			item_name=item.item_name
			# item_bom=frappe.db.get_value('Item',item.item_code,'default_bom')
			item_qty=item.qty
			
			stock_proj=frappe._dict({'item_code':item_code})
			col , vals=execute_proj_qty(stock_proj)
			for raw in vals:
				sum+=raw[16]

			month_labels = ["January", "February", "March", "April", "May", "June",
					"July", "August", "September", "October", "November", "December"] 

			if month in month_labels:
				if Type=="Committed":
					processed_item = {
						"item": doc.name,
						'code': item_code,
						'item_name':item_name,
						'avil_qty':sum,
						f"{month}_com":item_qty,
						f"{month}": item_qty,
					}

			if month in month_labels: 
				if Type=="Rolling": 
					posting_date
					processed_item = {
						"item": doc.name,
						'code': item_code,
						'item_name':item_name,
						'avil_qty':sum,
						f"{month}_rol":item_qty,
						f"{month}":item_qty,
					}
			
			if month in month_labels:
				if Type=="Annual and Updated Annual":
					processed_item = {
						"item": doc.name,
						'code': item_code,
						'item_name':item_name,
						'avil_qty':sum,
						f"{month}_ann":item_qty,
						f"{month}":item_qty,
					}
			
			processed_data.append(processed_item)
	return processed_data
	


# data = frappe._dict({'bom':item_bom,'qty_to_make':item_qty,'show_exploded_view':True})
			# column,items=execute_base_report(data)
			# aggregated_items = {} 
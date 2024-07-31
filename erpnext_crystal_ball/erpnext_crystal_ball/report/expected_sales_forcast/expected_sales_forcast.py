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
		
	return columns

def get_data(filters=None):

	return get_processed_date(filters)
	
	
def get_processed_date(filters=None):
	if filters:
		
		ExpectedSales_list=[]
		processed_data = []
		processed_items_dict = {}
		
		
		month_labels = ["January", "February", "March", "April", "May", "June",
						"July", "August", "September", "October", "November", "December"]

		not_rolling_list=frappe.db.get_list("Expected Sales",fields=['name',],
									  filters={'type': ['!=', 'Rolling'],'docstatus':1,},pluck='name')
		
		for mon in month_labels:
			max_rolling_list = frappe.db.get_list("Expected Sales",fields=["max(name) as name",'month',"max(posting_date) as date"],
										filters={'docstatus':1,"type": 'Rolling',"month":mon})
			
			for rolling in max_rolling_list:

				if rolling.get('name') !=None: 
					ExpectedSales_list.append(rolling.get('name'))
		
		ExpectedSales_list.extend(not_rolling_list)

		for name in ExpectedSales_list:
			
			doc=frappe.get_doc("Expected Sales",name)
			actual_qty=0
			for item in doc.item_records:
				doc.month
				Type=doc.type
				item_code=item.item_code
				item_name=item.item_name
				item_qty=item.qty
				stock_proj=frappe._dict({'item_code':item_code})
				cols , vals=execute_proj_qty(stock_proj)
				for raw in vals:
					actual_qty+=raw[7] 
				
				for month in month_labels:
					if doc.month==month :
						if item_code not in processed_items_dict:
							
							processed_items_dict[item_code] = {
								
								'code': item_code,
								'item_name':item_name,
								'avil_qty':actual_qty,
								**{f"{month}_com":0 for month in month_labels}, # ** used for unpacking dict 
								**{f"{month}_rol":0 for month in month_labels},
								**{f"{month}_ann":0 for month in month_labels},
								**{f"{month}":0 for month in month_labels}	
							}
						if doc.type == 'Committed':
							processed_items_dict[item_code][f"{doc.month}_com"] += item_qty
							processed_items_dict[item_code][f"{doc.month}"]=processed_items_dict[item_code][f"{doc.month}_com"]
						elif doc.type == 'Annual':
							processed_items_dict[item_code][f"{doc.month}_ann"] += item_qty
							processed_items_dict[item_code][f"{doc.month}"]=processed_items_dict[item_code][f"{doc.month}_ann"]
						elif doc.type == 'Rolling':
							processed_items_dict[item_code][f"{doc.month}_rol"] += item_qty
							if processed_items_dict[item_code][f"{doc.month}_ann"] == 0 : 
								processed_items_dict[item_code][f"{doc.month}"]=processed_items_dict[item_code][f"{doc.month}_rol"]
						
		processed_data=list(processed_items_dict.values())
		return processed_data


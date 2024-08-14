# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.report.stock_projected_qty.stock_projected_qty import execute as execute_proj_qty
from erpnext_crystal_ball.erpnext_crystal_ball.report.expected_sales_forcast.expected_sales_forcast import execute as execute_exp_forcast
from erpnext.manufacturing.report.bom_stock_calculated.bom_stock_calculated import execute as get_raw_matrial
import datetime
from datetime import datetime ,timedelta


def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
	return [
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
			"label": _("Avaliable Qty"),
			"fieldname": "avail_qty",
			"fieldtype": "Float",
			"width": 140,
			"convertible": "qty",
		},
		{
			"label": _("Required Qty"),
			"fieldname": "req_qty",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty",
		},
		
	]

# { "ITM-000" : {
#     "lead_time": 7,
#     "coverage_days": 30,
#     "order_day" or "lead_time_start_date": "2021-01-01",
#     "end_lead_time" = "coverage_days_start_date": "2021-01-10",
#     "coverage_days_end_date": "2021-01-17",
#     "total_qty_in_coverage_days": 300,   // This is the tricky number
#     "FG": {
#         "FG_ITM-CODE-01" : {
#             "fg_qty_in_coverage_day": 10,=== req raw_qty for fg
#             "qty_per_unit": 1,
#             "stock_qty_required_for_coverage_days": 30, // raw qty * fg_qty_in_coverage_day
#             "BOM": "BOM-ITM-CODE" //For Reference
#         },
#         "FG_ITM-CODE-02" : {
#             "fg_qty_in_coverage_day": 10, == req raw_qty for fg
#             "qty_per_unit": 2,
#             "stock_qty_required_for_coverage_days": 30, // raw qty * fg_qty_in_coverage_day
#             "BOM": "BOM-ITM-CODE" //For Reference
#         }
#     }
# }
# }


def get_data(filters=None):
	
	month_labels = ["January", "February", "March", "April", "May", "June",
					"July", "August", "September", "October", "November", "December"]

	processed_items = []

	# Retrieve  date from filter
	filter_date_str = filters.get('order_date')
	filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d')
	
	# Fetch the list of items
	item_list = frappe.db.get_list('Item', fields=['name'],filters={'item_group': ['not in', ['FG', 'SR', 'Fixed Assets']]} 
								,pluck='name')
	fg_item_list=frappe.db.get_list('Item', fields=['name'],filters={'item_group': ['=', 'FG']} 
								,pluck='name')
	

	# Get forecast data
	exp_forcast = frappe._dict({'fiscal_year': '2024-2025'})
	col, fg_forcast = execute_exp_forcast(exp_forcast)
	data_structure={}
	for item_fg in fg_forcast:
		fg_item_code = item_fg['code']
		default_bom =fetch_default_bom(fg_item_code)

		cover_days,lead_time=get_lead_time(item_fg,default_bom)

		start_coverage_date= filter_date +timedelta(days=lead_time)    # filter_date + lead_time
		end_coverage_date=start_coverage_date+timedelta(days=cover_days)
		order_month_name = start_coverage_date.strftime('%B')         # Get full month name
		
		# Get for FG all Raw Maretial items 
		processes_raw_material(item_fg,order_month_name,default_bom,data_structure)

	for raw_material_code,raw_material_info in data_structure.items():
		lead_time=raw_material_info.get('lead_time')
		coverage_days=raw_material_info.get('coverage_days')
		avilable_qty=raw_material_info.get('avil_qty')
		description=raw_material_info.get('description')

		fgs=raw_material_info.get('FGs',{})

		for fg_item,fg_info in fgs.items():
			req_qty = fg_info.get('fg_qty_in_coverage_day',0)
			processed_item = {
									'raw_item':raw_material_code,
									'description': description,
									'lead_time':lead_time,
									'coverage_days':coverage_days,
									'avail_qty':avilable_qty,
									'req_qty':req_qty
								}
			processed_items.append(processed_item)
				
	return processed_items
			
def get_lead_time(item_fg,default_bom):
	"""Fetches Lead time and Coverage days for each Raw material."""
	data_dict = {
			'bom': default_bom,
			'qty_to_make': 1,
			'show_exploded_view': True
			}
		
	columns , items=get_raw_matrial(frappe._dict(data_dict))
	
	fg_item_code=item_fg['code']
	for item in items:
		raw_material_code=item[0]
		lead_time=frappe.db.get_value('Item',raw_material_code,'lead_time_days')
		coverage_days=frappe.db.get_value('Item',raw_material_code,'custom_coverage_days')
		return coverage_days,lead_time
		
def fetch_default_bom(fg_item_code):
    """Fetches the default BOM for the given FG item code."""
    return frappe.db.get_value('Item', fg_item_code, 'default_bom')

def fetch_fg_qty(item_fg, month):
	"""fetch qty for each FG according to month."""
	quantity = item_fg[month]
	if quantity > 0:
		print(f"Month: {month}, Quantity: {quantity}")
	return quantity
		
def processes_raw_material(item_fg: dict,month,default_bom,data_structure) -> dict:
	"""Processes data of raw_material for each FG."""
	quantity=fetch_fg_qty(item_fg,month)
	data_dict = {
			'bom': default_bom,
			'qty_to_make': quantity,
			'show_exploded_view': True
			}
		
	columns , items=get_raw_matrial(frappe._dict(data_dict))
	
	fg_item_code=item_fg['code']
	for item in items:
		raw_material_code=item[0]
		lead_time=frappe.db.get_value('Item',raw_material_code,'lead_time_days')
		coverage_days=frappe.db.get_value('Item',raw_material_code,'custom_coverage_days')
		description=item[1]
		qty_per_unit = item[4]
		avil_qty=item[5]
		raw_qty_req = quantity * qty_per_unit
		
		if raw_material_code not in data_structure:
			data_structure[raw_material_code] = {
				'lead_time': lead_time,
				'coverage_days': coverage_days,
				'avil_qty':avil_qty,
				'description':description,
				# 'order_date': None,
				# 'total_qty_in_coverage_days': 0,
				'FGs': {}
			}
		if fg_item_code not in data_structure[raw_material_code]['FGs']:
			data_structure[raw_material_code]['FGs'][fg_item_code] = {
				'fg_qty_in_coverage_day': raw_qty_req,
				# 'qty_per_unit': qty_per_unit,
				# 'stock_qty_required_for_coverage_days': 0,  # Placeholder value
				'BOM': default_bom
			}


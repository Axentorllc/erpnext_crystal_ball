# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.report.stock_projected_qty.stock_projected_qty import execute as execute_proj_qty
from erpnext_crystal_ball.erpnext_crystal_ball.report.expected_sales_forcast.expected_sales_forcast import execute as execute_exp_forcast
from erpnext.manufacturing.report.bom_stock_calculated.bom_stock_calculated import execute as get_raw_matrial
import datetime
from datetime import datetime ,timedelta
from dateutil.relativedelta import relativedelta


class AdjustedQty:

	def __init__(self,filters):
		self.filters=filters
		self.data_structure={}
		self.raw_list=[]
		self.pack_list=[]
		self.items_dicts=[]
		self.months=self.get_months_range(self.filters.get('from_date'),self.filters.get('to_date'))
		self.group=self.filters.get('material_type')
		self.processed_materials=[]
		self.material_list=[]

		# Fetch the list of RAW and PACK items
		self.raw_item_list=frappe.db.get_list('Item', fields=['name'],filters={'item_group': ['=', 'RAW']} 
									,pluck='name')
		self.pack_item_list=frappe.db.get_list('Item', fields=['name'],filters={'item_group': ['=', 'PACK']} 
								,pluck='name')
	

	def get_months_range(self,from_date_str,to_date_str):

		"""Generate a list of month names between the given date range."""

		from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
		to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

		months=[]
		current_date=from_date
		while current_date <= to_date:
			month_name= current_date.strftime('%B')
			if month_name not in months:
				months.append(month_name)
			current_date += relativedelta(months=1)
		
		return months


	def get_columns(self):

		"""Define the columns for the report"""

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
				"label": _("Avaliable Qty"),
				"fieldname": "avail_qty",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			
		]
		for month in self.months:
			columns.append({
				"label": _(f"{month} Required Qty"),
				"fieldname": f"{month}_req_qty",
				"fieldtype": "Float",
				"width": 120,
				"convertible": "qty",
			},)
		
		return columns


	def get_data(self):

		"""Fetch and process the required data based on filters."""

		# Get forecast data
		exp_forcast = frappe._dict({'fiscal_year': '2024-2025'})
		cols, fg_forcast = execute_exp_forcast(exp_forcast)

		for month in self.months:
			for item_fg in fg_forcast:
				item_code=item_fg['code']
				default_bom=frappe.db.get_value('Item',item_code,'default_bom')
				quantity=self.get_fg_qty(item_fg,month)

				data_dict={
					'bom':default_bom,
					'qty_to_make': quantity,
					'show_exploded_view': True,
				}

				columns , items= get_raw_matrial(frappe._dict(data_dict))
				self.items_dicts= self.map_raw_material(columns,items)
				self.processes_raw_material(item_fg,month,quantity)

		self.material_list = self.filter_by_material_type()
		self.set_processed_materials()

		print(self.data_structure)
		return self.processed_materials


	def set_processed_materials(self):

		"""
		This function iterates over the raw material codes in the data structure, checks if
		they are in the current material list, and then creates a dictionary for each material
		with its details, including available quantity and required quantities for each month.
		"""
		for raw_material_code,raw_material_info in self.data_structure.items():

			if raw_material_code in self.material_list:

				# lead_time=raw_material_info.get('lead_time')
				# coverage_days=raw_material_info.get('coverage_days')
				avilable_qty=raw_material_info.get('avil_qty')
				description=raw_material_info.get('description')
				

				processed_item = {
							'raw_item':raw_material_code,
							'description': description,
							# 'lead_time':lead_time,
							# 'coverage_days':coverage_days,
							'avail_qty':avilable_qty,
				}

				fgs=raw_material_info.get('FGs',{})
				
				for month in self.months:
						
					total_raw_material = raw_material_info.get('total_months_req')
					req_qty=total_raw_material.get(f'total_{month}_req_qty')
					processed_item[f'{month}_req_qty'] = req_qty

				self.processed_materials.append(processed_item)


	def filter_by_material_type(self):

		"""
		Returns:
			list: A list of filtered material codes based on the selected material type.
		"""

		if self.group == 'raw material':
			self.material_list = self.raw_list  # Show only raw materials
		elif self.group == 'pack material':
			self.material_list = self.pack_list  # Show only pack materials
		else:
			self.material_list =self.raw_list + self.pack_list  # Show all if no specific group selected

		return self.material_list


	def get_fg_qty(self,item_fg,month):

		"""
		Get the quantity required for fg for a specific month.
		Args:
			item_fg : item code.
			month : The month for which quantity is required.
			"""

		quantity = item_fg.get(month, 0)
		return quantity


	def processes_raw_material(self,item_fg,month,quantity):
		"""
		get all the required data for each raw material,
		calc req_qty according to each month
		"""
		fg_item_code=item_fg['code']
		
		for item in self.items_dicts:
			raw_material_code=item.get('item')
			description=item.get('description')
			avil_qty=item.get('available_qty')
			qty_per_unit=item.get('qty_per_unit')

			# lead_time=frappe.db.get_value('Item',raw_material_code,'lead_time_days')
			# coverage_days=frappe.db.get_value('Item',raw_material_code,'custom_coverage_days')
			
			raw_required_qty=quantity * qty_per_unit
			
			self.classify_raw_material(raw_material_code)

			if raw_material_code not in self.data_structure:
				self.data_structure[raw_material_code] = {
					# 'lead_time': lead_time,
					# 'coverage_days': coverage_days,
					'avil_qty':avil_qty,
					'description':description,
					'FGs':{
						fg_item_code:{
						f'{month}_req_qty': raw_required_qty
						}
					}, 
					'total_months_req':{
						f'total_{month}_req_qty': raw_required_qty
					}
				}
				
			else:
				
				if fg_item_code not in self.data_structure[raw_material_code]['FGs']:
					self.data_structure[raw_material_code]['FGs'][fg_item_code] = {}

				else:
					self.data_structure[raw_material_code]['FGs'][fg_item_code][f'{month}_req_qty'] = raw_required_qty
					self.data_structure[raw_material_code]['total_months_req'][f'total_{month}_req_qty'] += raw_required_qty
					
				
	def classify_raw_material(self,raw_material_code):

		"""
		Classify the material as either raw or pack based on its item group.
		"""

		if raw_material_code in self.raw_item_list and raw_material_code not in self.raw_list:
			self.raw_list.append(raw_material_code)

		elif raw_material_code in self.pack_item_list and raw_material_code not in self.pack_list:
			self.pack_list.append(raw_material_code)


	def map_raw_material(self,columns,items):

		"""
		Map raw material data to its respective fieldnames.

		Args:
			columns (list): The columns of data.
			items (list): The raw materials data.

		Returns:
			list: Mapped raw materials.
		"""

		fieldnames=[column['fieldname'] for column in columns]
		for item in items:
			self.items_dicts.append(dict(zip(fieldnames,item)))
		
		return self.items_dicts

		
def execute(filters=None):

	"""
	Execute the report generation process by initializing the AdjustedQty class.
	
			{ "ITM-000" : {
				"lead_time": 7,
				"coverage_days": 30,
				"order_day" or "lead_time_start_date": "2021-01-01",
				"end_lead_time" = "coverage_days_start_date": "2021-01-10",
				"coverage_days_end_date": "2021-01-17",
				"total_qty_in_coverage_days": 300,   // This is the tricky number
				"FG": {
					"FG_ITM-CODE-01" : {
						"fg_qty_in_coverage_day": 10,=== req raw_qty for fg
						"qty_per_unit": 1,
						"stock_qty_required_for_coverage_days": 30, // raw qty * fg_qty_in_coverage_day
						"BOM": "BOM-ITM-CODE" //For Reference
						"jan_req_qty": 10
						"Feb_req_qty": 20
						
					},
					"FG_ITM-CODE-02" : {
						"fg_qty_in_coverage_day": 10, == req raw_qty for fg
						"qty_per_unit": 2,
						"stock_qty_required_for_coverage_days": 30, // raw qty * fg_qty_in_coverage_day
						"BOM": "BOM-ITM-CODE" //For Reference,
						"jan_req_qty" : 50
						"Feb_req_qty" : 60
					}
				},
				"total_qty_by_month": {
					"total_feb_req_qty": 70,
					"total_jan_req_qty": 60,
					....
				}
			}
	"""

	adjusted = AdjustedQty(filters)
	columns = adjusted.get_columns()
	data = adjusted.get_data()
	return columns, data

				
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


class AdjustedStockQty:

	def __init__(self,filters):
		self.filters=filters
		self.data_structure={}
		self.raw_list=[]
		self.pack_list=[]
		today = datetime.today()
		self.months=self.get_months_range(self.filters.get('from_date') ,self.filters.get('to_date'))
		self.group=self.filters.get('material_type')
		self.fiscal_year=self.filters.get('fiscal_year')
		self.safety_stock=self.filters.get('safety_stock')
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
				"label": _("Lead Time"),
				"fieldname": "lead_time",
				"fieldtype": "Data",
				"width": 140,
			},
			{
				"label": _("Coverage Days"),
				"fieldname": "coverage_days",
				"fieldtype": "Data",
				"width": 140,
			},

			{
				"label": _("Avaliable Qty"),
				"fieldname": "avail_qty",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			{
				"label": _("Ordered Qty"),
				"fieldname": "ordered_qty",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			{
				"label": _("Reserved Qty"),
				"fieldname": "reserved_qty",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			
			{
				"label": _("Actual Safety Qty"),
				"fieldname": "actual_qty",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",
			},
			
		]
		if self.safety_stock:
			columns.insert(7,{
				"label": _("Safety Stock"),
				"fieldname": "safety_stock",
				"fieldtype": "Float",
				"width": 140,
				"convertible": "qty",

			})
		for month in self.months:
			columns.append({
				"label": _(f"{month} Required Qty"),
				"fieldname": f"{month}_req_qty",
				"fieldtype": "Float",
				"width": 120,
				"convertible": "qty",
			},)
			columns.append({
				"label": _(f"{month} Difference Qty"),
				"fieldname": f"{month}_diff_qty",
				"fieldtype": "Float",
				"width": 120,
				"convertible": "qty",
			})

		
		return columns


	def get_data(self):

		"""Fetch and process the required data based on filters."""

		# Get forecast data
		exp_forcast = frappe._dict({'fiscal_year': self.fiscal_year})
		cols, fg_forcast = execute_exp_forcast(exp_forcast)
		

		for month in self.months:
			
			self.get_forcast_data(month,fg_forcast)

		self.material_list = self.filter_by_material_type()
		self.set_processed_materials()

		return self.processed_materials


	def get_forcast_data(self,month,fg_forcast):

		for item_fg in fg_forcast:
			items_dicts=[]
			item_code=item_fg['code']
			default_bom=frappe.db.get_value('Item',item_code,'default_bom')
			quantity=item_fg.get(month)

			data_dict={
				'bom':default_bom,
				'qty_to_make': quantity,
				'show_exploded_view': True,
			}

			columns , items= get_raw_matrial(frappe._dict(data_dict))
			items_dicts= self.map_raw_material(columns,items,items_dicts)
			self.processes_raw_material(item_code,month,quantity,items_dicts)


	def set_processed_materials(self):

		"""
		This function iterates over the raw material codes in the data structure, checks if
		they are in the current material list, and then creates a dictionary for each material
		with its details, including available quantity and required quantities for each month.
		"""
		for raw_material_code,raw_material_info in self.data_structure.items():

			if raw_material_code in self.material_list:

				lead_time=raw_material_info.get('lead_time')
				coverage_days=raw_material_info.get('coverage_days')
				avilable_qty=raw_material_info.get('avil_qty')
				description=raw_material_info.get('description')
				ordered_qty=raw_material_info.get('ordered_qty')
				reserved_qty=raw_material_info.get('reserved_qty')
				safety_stock=raw_material_info.get('safety_stock')
				actual_qty=raw_material_info.get('actual_qty')
				

				processed_item = {
							'raw_item':raw_material_code,
							'description': description,
							'lead_time':lead_time,
							'coverage_days':coverage_days,
							'avail_qty':avilable_qty,
							'ordered_qty':ordered_qty,
							'reserved_qty':reserved_qty,
							'safety_stock':safety_stock,
							'actual_qty':actual_qty
				}

				fgs=raw_material_info.get('FGs',{})
				previous_diff_qty = actual_qty

				self.set_calculated_material_qty(raw_material_info,processed_item,previous_diff_qty)
				
				
	def set_calculated_material_qty(self,raw_material_info,processed_item,previous_diff_qty):

		for month in self.months:
					
			total_raw_material = raw_material_info.get('total_months_req')
			req_qty=total_raw_material.get(f'total_{month}_req_qty')

			diff_qty = previous_diff_qty - req_qty

			processed_item[f'{month}_req_qty'] = req_qty
			processed_item[f'{month}_diff_qty'] = diff_qty

			previous_diff_qty = diff_qty

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


	
	def processes_raw_material(self,item_code,month,quantity,items_dicts):
		"""
		get all the required data for each raw material,
		calc req_qty according to each month
		"""
		fg_item_code=item_code

		for item in items_dicts:
			raw_material_code=item.get('item')
			description=item.get('description')
			avil_qty=item.get('available_qty')
			qty_per_unit=item.get('qty_per_unit')

			raw_required_qty = quantity * qty_per_unit

			ordered_qty,reserved_qty=self.get_projected_stock(raw_material_code)

			safety_stock , lead_time , coverage_days = frappe.db.get_value('Item',
						raw_material_code,['safety_stock','lead_time_days','custom_coverage_days'])
			
			actual_safety_qty=self.calculate_actual_safety_quantity(safety_stock,avil_qty,ordered_qty,reserved_qty)

			self.classify_raw_material(raw_material_code)

			if raw_material_code not in self.data_structure:
				self.data_structure[raw_material_code] = {
					'avil_qty':avil_qty,
					'description':description,
					'lead_time': lead_time,
					'coverage_days': coverage_days,
					'ordered_qty':ordered_qty,
					'reserved_qty':reserved_qty,
					'safety_stock':safety_stock,
					'actual_qty':actual_safety_qty,
					f'{month}_diff_qty':0,

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
					
				if f'total_{month}_req_qty' not in self.data_structure[raw_material_code]['total_months_req']:
					self.data_structure[raw_material_code]['total_months_req'][f'total_{month}_req_qty']=0

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


	def map_raw_material(self,columns,items,items_dicts):

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
			items_dicts.append(dict(zip(fieldnames,item)))
		
		return items_dicts


	def get_projected_stock(self,raw_material_code):

		ordered_qty=0
		reserved_qty=0

		projected_data=frappe.get_list('Bin',
					filters={'item_code':raw_material_code},fields=['ordered_qty','reserved_qty'])
	    
		for row in projected_data:
			ordered_qty+=row.get('ordered_qty')
			reserved_qty+=row.get('reserved_qty')
		
		return ordered_qty, reserved_qty



	def calculate_actual_safety_quantity(self,safety_stock,avil_qty,ordered_qty,reserved_qty):

		actual_safety_qty=0

		if self.safety_stock:
			actual_safety_qty=(avil_qty + ordered_qty + reserved_qty) - safety_stock
		else:
			actual_safety_qty=(avil_qty + ordered_qty + reserved_qty)

		return actual_safety_qty

		
def execute(filters=None):

	"""
	Execute the report generation process by initializing the AdjustedQty class.
	
			{ "ITM-000" : {
				"avail_qty":1000
				"lead_time": 60,
				"coverage_days": 30,
				"Reservied_qty": 1000 , // from "stock projected qty"
				"order_qty":   500  ,   //  from "stock projected qty"
				"safty_stock_qty":200,       //  from hcpc master data
				
				"A.avail_qty":(avail_qty + Reservied_qty + order_qy ) - safty_stock

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

	adjusted = AdjustedStockQty(filters)
	columns = adjusted.get_columns()
	data = adjusted.get_data()
	return columns, data

				
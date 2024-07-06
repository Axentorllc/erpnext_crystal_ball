# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExpectedSales(Document):
	
	def validate(self):
		self.validate_fetching_item_name()
		self.fetch_item_records()
		self.validate_expected_date()
		
	def validate_fetching_item_name(self):
		
		for item in self.item_records:
			item_name=frappe.db.get_value('Item',item.item_code,'item_name')
			if not item_name:
				return
	
	def validate_expected_date(self):
		if self.expected_end<self.expected_date:
			frappe.throw("Please make sure that the Expected End is bigger")
    
	def fetch_item_records(self):
		Item_BOM=[]
		Item_QTY=[]
		is_selected=[]

		for item in self.item_records:
            
			id=item.idx
			item_code=item.item_code
			item_bom=frappe.db.get_value('Item',item.item_code,'default_bom')

			if item_code in is_selected:
				frappe.msgprint(f"The item code {item_code} is already in the list at raw{id} .")

			else:
				is_selected.append(item_code)
				Item_BOM.append(item_bom)
				Item_QTY.append(item.qty)
			
		return Item_BOM, Item_QTY
    

	
			

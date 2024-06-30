# Copyright (c) 2024, Carlos and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExpectedSales(Document):
	def validate(self):
		self.validate_fetching_item_name()
		
	def validate_fetching_item_name(self):
		
		item_name=frappe.db.get_value('Item',self.item_code,'item_name')
		if not item_name:
			frappe.throw(f"Item {item_name} not found or does not exist.")

